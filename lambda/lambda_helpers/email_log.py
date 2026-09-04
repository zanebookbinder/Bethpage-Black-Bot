import logging
import boto3
from boto3.dynamodb.conditions import Attr
from lambda_helpers.date_handler import EASTERN, now_eastern

logger = logging.getLogger(__name__)

EMAIL_LOG_TABLE_NAME = "bethpage-black-bot-email-log"

RECORD_TYPE_KEY = "record_type"
EMAIL_SENT_RECORD_TYPE = "email_sent"
REPORT_MARKER_RECORD_TYPE = "weekly_report_marker"
REPORT_MARKER_ID_PREFIX = "weekly-report-sent#"

TEE_TIME_KEYS = ("Date", "Time", "Players", "Holes")


class EmailLog:
    """Persists one record per tee time notification email so the weekly admin
    report can summarize what was sent.

    Records share a ``run_id`` (the Eastern timestamp of the lambda run that
    sent them), which is what lets the report collapse the several users
    notified about the same tee time in the same run into a single row.
    """

    def __init__(self, table=None):
        self.table = table if table is not None else boto3.resource("dynamodb").Table(
            EMAIL_LOG_TABLE_NAME
        )

    @staticmethod
    def build_run_id(run_time):
        """Eastern ISO timestamp (second precision) shared by every email in a
        run, e.g. '2026-08-20T14:18:30-04:00'."""
        return run_time.astimezone(EASTERN).replace(microsecond=0).isoformat()

    @staticmethod
    def _clean_tee_time(tee_time):
        """Store tee time fields as strings so Decimal/int/str differences from
        the scraper don't change how a slot is rendered or de-duplicated."""
        return {key: str(tee_time.get(key, "")) for key in TEE_TIME_KEYS}

    def record_email_sent(
        self, run_time, user_email, tee_times, backfilled=False, approximate=False
    ):
        run_id = self.build_run_id(run_time)
        item = {
            "id": f"{run_id}#{user_email}",
            RECORD_TYPE_KEY: EMAIL_SENT_RECORD_TYPE,
            "run_id": run_id,
            "sent_at": run_id,
            "sent_at_epoch": int(run_time.timestamp()),
            "user_email": user_email,
            "tee_times": [self._clean_tee_time(t) for t in tee_times],
        }
        if backfilled:
            item["backfilled"] = True
        if approximate:
            item["approximate"] = True

        self.table.put_item(Item=item)
        logger.debug(
            "Logged notification email to %s (%d tee times) for run %s",
            user_email,
            len(tee_times),
            run_id,
        )

    def get_emails_sent_since(self, cutoff):
        """All email_sent records with sent_at_epoch >= cutoff (a datetime)."""
        cutoff_epoch = int(cutoff.timestamp())
        scan_kwargs = {
            "FilterExpression": Attr(RECORD_TYPE_KEY).eq(EMAIL_SENT_RECORD_TYPE)
            & Attr("sent_at_epoch").gte(cutoff_epoch)
        }

        items = []
        while True:
            response = self.table.scan(**scan_kwargs)
            items.extend(response.get("Items", []))
            if "LastEvaluatedKey" in response:
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            else:
                break

        logger.info(
            "Found %d logged emails since %s", len(items), cutoff.isoformat()
        )
        return items

    def has_report_been_sent(self, week_key):
        response = self.table.get_item(Key={"id": REPORT_MARKER_ID_PREFIX + week_key})
        return "Item" in response

    def mark_report_sent(self, week_key, email_count):
        self.table.put_item(
            Item={
                "id": REPORT_MARKER_ID_PREFIX + week_key,
                RECORD_TYPE_KEY: REPORT_MARKER_RECORD_TYPE,
                "week_key": week_key,
                "sent_at": now_eastern().isoformat(),
                "email_count": email_count,
            }
        )
        logger.info("Marked weekly email report as sent for week of %s", week_key)
