"""
Backfill the bethpage-black-bot-email-log table with historical notification
emails, so the weekly report has data from before logging was added.

The CloudWatch logs for /aws/lambda/bethpage-black-bot record *who* was emailed
and *how many* new tee times they got ("Sending tee time notification to X with
N new times"), but not which slots. The slots are recovered by replaying the
bot's diffing algorithm against the tee-times table, which stores a full
snapshot of the site on every run:

  1. Pull every "Sending tee time notification" line from CloudWatch Logs
     Insights and group it by @requestId — one group per lambda run.
  2. Match each run to the tee-times snapshot it published.
  3. Replay `filter_tee_times_for_user` + `remove_existing_tee_times` over those
     snapshots in order, resetting the "already seen" set each UTC day exactly
     as `get_available_times_by_day` does.
  4. Cross-check the replayed slot count against the count in the log line.

Because only *current* user configs are available, a user who changed their
settings mid-window can replay to a different count than the log recorded.
Those records are still written, but flagged with `approximate: True` so they
are easy to spot in the table. The script prints a match rate at the end.

Run from the lambda/ directory:
    python backfill_email_log.py --days 30 --dry-run
    python backfill_email_log.py --days 30
"""

import argparse
import bisect
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import boto3
import holidays
from boto3.dynamodb.conditions import Attr

from lambda_helpers.bethpage_black_config import BethpageBlackBotConfig
from lambda_helpers.date_handler import EASTERN
from lambda_helpers.dynamo_db_connection import (
    ALL_TEE_TIMES_OBJECT_ID,
    TEE_TIMES_TABLE_NAME,
    DynamoDBConnection,
)
from lambda_helpers.email_log import EMAIL_LOG_TABLE_NAME, EmailLog
from lambda_helpers.tee_time_filterer import TeeTimeFilterer

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("lambda_helpers").setLevel(logging.WARNING)

LOG_GROUP_NAME = "/aws/lambda/bethpage-black-bot"
LOG_QUERY = """
fields @timestamp, @requestId
| filter @message like /Sending tee time notification to/
| parse @message "Sending tee time notification to * with * new times" as user_email, new_count
| sort @timestamp asc
| limit 10000
"""
LOG_QUERY_RESULT_LIMIT = 10000

# How far after a run's first email the matching tee-times snapshot may land.
# Runs are 3 minutes apart and time out at 90s, so this can't straddle two runs.
SNAPSHOT_MATCH_WINDOW_SECONDS = 180


def parse_insights_timestamp(value):
    """Logs Insights returns '2026-08-20 18:07:15.233' in UTC."""
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)


def parse_snapshot_id(snapshot_id):
    """tee-times ids are naive UTC `datetime.now().isoformat()` strings."""
    return datetime.fromisoformat(snapshot_id).replace(tzinfo=timezone.utc)


class HistoricalTeeTimeFilterer(TeeTimeFilterer):
    """TeeTimeFilterer with 'today' pinned to the run being replayed, so the
    out-of-state booking window and the implied year are historically correct."""

    def __init__(self, db_connection, years):
        super().__init__(db_connection=db_connection)
        self.as_of_date = None

        self.holiday_dates = set()
        for year in years:
            us_holidays = holidays.UnitedStates(years=year)
            self.holiday_dates |= {
                f"{date.month}/{date.day}/{date.year}"
                for date, name in us_holidays.items()
                if "Veterans Day" not in name
            }

    def is_within_in_state_booking_window(self, user_config, date_obj):
        if user_config.in_state_golfer:
            return True
        return date_obj <= self.as_of_date + timedelta(days=5)

    def get_user_config_as_object(self, user_email):
        """Config-less users are skipped in production now, but over the period
        being replayed they were notified on BethpageBlackBotConfig's defaults.
        Reproduce that, or their historical emails replay as zero tee times."""
        return BethpageBlackBotConfig(self.db_table.get_user_config(user_email))

    def parse_date_string(self, date_str):
        parts = date_str.split()
        day_of_week = parts[0]
        month = parts[1]
        day = self.date_handler.strip_ordinal_suffix(parts[2])

        date_obj = datetime.strptime(
            f"{month} {day} {self.as_of_date.year}", "%B %d %Y"
        ).date()
        # Tee times are only ever a few days out, so a date well behind the run
        # means the listing wrapped into the next year.
        if date_obj < self.as_of_date - timedelta(days=30):
            date_obj = date_obj.replace(year=self.as_of_date.year + 1)
        return day_of_week, date_obj


class CachingConfigConnection:
    """Wraps DynamoDBConnection so each user's config is fetched once, not once
    per replayed run."""

    def __init__(self, db_connection):
        self.db_connection = db_connection
        self._cache = {}

    def get_user_config(self, email):
        if email not in self._cache:
            self._cache[email] = self.db_connection.get_user_config(email)
            if self._cache[email] is None:
                logger.warning(
                    "  ! %s has no config row — replaying on defaults, which is "
                    "what the bot did at the time",
                    email,
                )
        return self._cache[email]


def fetch_notification_log_lines(logs_client, start, end):
    """Run the Insights query one UTC day at a time to stay under the 10k
    result cap, returning [{timestamp, request_id, user_email, new_count}]."""
    rows = []
    day_start = start
    while day_start < end:
        day_end = min(day_start + timedelta(days=1), end)
        rows.extend(_run_insights_query(logs_client, day_start, day_end))
        day_start = day_end
    return rows


def _run_insights_query(logs_client, start, end):
    query_id = logs_client.start_query(
        logGroupName=LOG_GROUP_NAME,
        startTime=int(start.timestamp()),
        endTime=int(end.timestamp()),
        queryString=LOG_QUERY,
        limit=LOG_QUERY_RESULT_LIMIT,
    )["queryId"]

    while True:
        response = logs_client.get_query_results(queryId=query_id)
        if response["status"] in ("Complete", "Failed", "Cancelled", "Timeout"):
            break
        time.sleep(1)

    if response["status"] != "Complete":
        raise RuntimeError(
            f"CloudWatch query for {start.date()} ended with status {response['status']}"
        )

    results = response["results"]
    if len(results) >= LOG_QUERY_RESULT_LIMIT:
        logger.warning(
            "  ! Hit the %d-result cap on %s — some emails may be missing",
            LOG_QUERY_RESULT_LIMIT,
            start.date(),
        )

    rows = []
    for result in results:
        fields = {field["field"]: field["value"] for field in result}
        if "user_email" not in fields:
            continue
        rows.append(
            {
                "timestamp": parse_insights_timestamp(fields["@timestamp"]),
                "request_id": fields.get("@requestId", fields["@timestamp"]),
                "user_email": fields["user_email"].strip(),
                "new_count": int(fields.get("new_count", 0)),
            }
        )

    logger.info("  %s: %d notification emails", start.date(), len(rows))
    return rows


def group_log_lines_into_runs(rows):
    """One run per lambda request id, ordered by when its first email went out."""
    by_request = defaultdict(list)
    for row in rows:
        by_request[row["request_id"]].append(row)

    runs = []
    for request_id, request_rows in by_request.items():
        runs.append(
            {
                "request_id": request_id,
                "run_time": min(r["timestamp"] for r in request_rows),
                "users": [
                    {"user_email": r["user_email"], "new_count": r["new_count"]}
                    for r in sorted(request_rows, key=lambda r: r["timestamp"])
                ],
            }
        )

    return sorted(runs, key=lambda run: run["run_time"])


def fetch_tee_time_snapshots(start, end):
    """[(timestamp, tee_times)] from the tee-times table, oldest first."""
    table = boto3.resource("dynamodb").Table(TEE_TIMES_TABLE_NAME)
    # Snapshot ids are ISO timestamps, so a lexicographic range is a time range.
    scan_kwargs = {
        "FilterExpression": Attr("id").between(
            start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S")
        ),
        "ProjectionExpression": "#pk, " + ALL_TEE_TIMES_OBJECT_ID,
        "ExpressionAttributeNames": {"#pk": "id"},
    }

    snapshots = []
    while True:
        response = table.scan(**scan_kwargs)
        for item in response.get("Items", []):
            try:
                snapshot_time = parse_snapshot_id(item["id"])
            except ValueError:
                continue  # non-timestamp ids like latest-tee-times
            snapshots.append((snapshot_time, item.get(ALL_TEE_TIMES_OBJECT_ID) or []))
        if "LastEvaluatedKey" in response:
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        else:
            break

    snapshots.sort(key=lambda s: s[0])
    logger.info("Loaded %d tee time snapshots", len(snapshots))
    return snapshots


def find_snapshot_for_run(snapshots, snapshot_times, run_time):
    """The snapshot a run published. `publish_teetimes` is the last thing
    `get_new_tee_times` does, so it lands seconds *before* the run's emails —
    hence the most recent snapshot at or before the first email."""
    index = bisect.bisect_right(snapshot_times, run_time) - 1
    if index < 0:
        return None
    snapshot_time, tee_times = snapshots[index]
    if (run_time - snapshot_time).total_seconds() > SNAPSHOT_MATCH_WINDOW_SECONDS:
        return None
    return tee_times


def replay_runs(runs, snapshots, filterer):
    """Reconstruct each run's per-user tee times, mirroring BethpageBlackBot."""
    snapshot_times = [s[0] for s in snapshots]
    results = []
    already_seen = []
    current_utc_date = None

    for run in runs:
        # Deliberately the UTC date, not the Eastern one: over the period being
        # replayed, get_available_times_by_day() compared against
        # datetime.now().date() in a UTC lambda, so that is where the bot
        # actually reset. Everything we *store* is stamped Eastern.
        run_date = run["run_time"].astimezone(timezone.utc).date()
        if run_date != current_utc_date:
            current_utc_date = run_date
            already_seen = []

        tee_times = find_snapshot_for_run(snapshots, snapshot_times, run["run_time"])
        if tee_times is None:
            logger.warning(
                "  ! No snapshot within %ds of run %s — slots unknown",
                SNAPSHOT_MATCH_WINDOW_SECONDS,
                EmailLog.build_run_id(run["run_time"]),
            )
            for user in run["users"]:
                results.append(
                    {
                        "run_time": run["run_time"],
                        "user_email": user["user_email"],
                        "tee_times": [],
                        "approximate": True,
                    }
                )
            continue

        # Same reasoning as run_date: the bot's "today" was the UTC one.
        filterer.as_of_date = run_date
        newly_sent = []

        for user in run["users"]:
            filtered = filterer.filter_tee_times_for_user(tee_times, user["user_email"])
            new_tee_times = filterer.remove_existing_tee_times(filtered, already_seen)
            results.append(
                {
                    "run_time": run["run_time"],
                    "user_email": user["user_email"],
                    "tee_times": new_tee_times,
                    "approximate": len(new_tee_times) != user["new_count"],
                }
            )
            for tee_time in new_tee_times:
                if tee_time not in newly_sent:
                    newly_sent.append(tee_time)

        already_seen.extend(newly_sent)

    return results


def write_records(records):
    table = boto3.resource("dynamodb").Table(EMAIL_LOG_TABLE_NAME)
    with table.batch_writer() as batch:
        email_log = EmailLog(table=batch)
        for record in records:
            email_log.record_email_sent(
                record["run_time"],
                record["user_email"],
                record["tee_times"],
                backfilled=True,
                approximate=record["approximate"],
            )


def run(days, dry_run):
    end = datetime.now(timezone.utc)
    # Aligned to UTC midnight so the replay sees each day's emails from the top,
    # which is where the bot's "already seen" state reset over this period.
    start = (end - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    logger.info(
        "Backfilling %s → %s (Eastern)\n",
        start.astimezone(EASTERN).isoformat(),
        end.astimezone(EASTERN).isoformat(),
    )

    logs_client = boto3.client("logs", region_name="us-east-1")
    rows = fetch_notification_log_lines(logs_client, start, end)
    if not rows:
        logger.info("\nNo notification emails found in that window.")
        return

    runs = group_log_lines_into_runs(rows)
    logger.info("\n%d emails across %d runs", len(rows), len(runs))

    snapshots = fetch_tee_time_snapshots(start - timedelta(minutes=10), end)

    db_connection = CachingConfigConnection(DynamoDBConnection())
    years = sorted({start.year, end.year, end.year + 1})
    filterer = HistoricalTeeTimeFilterer(db_connection, years)

    records = replay_runs(runs, snapshots, filterer)

    exact = sum(1 for r in records if not r["approximate"])
    logger.info(
        "\nRecovered exact tee time slots for %d/%d emails (%.0f%%); "
        "%d flagged approximate.",
        exact,
        len(records),
        100 * exact / len(records) if records else 0,
        len(records) - exact,
    )

    if dry_run:
        logger.info("\n--- dry run, nothing written. Sample: ---")
        for record in records[:10]:
            slots = ", ".join(
                f"{t.get('Date')} {t.get('Time')}" for t in record["tee_times"]
            )
            logger.info(
                "%s  %-32s %s%s",
                EmailLog.build_run_id(record["run_time"]),
                record["user_email"],
                slots or "(unknown)",
                "  [approx]" if record["approximate"] else "",
            )
        return

    write_records(records)
    logger.info("\nWrote %d records to the email log table.", len(records))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days", type=int, default=7, help="how many days back to backfill"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be written without writing it",
    )
    args = parser.parse_args()
    run(days=args.days, dry_run=args.dry_run)
