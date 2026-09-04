"""
Send the "Bethpage Black Bot Email Report" right now, for whatever emails were
logged in the last 7 days. Ignores the Sunday-after-7pm schedule, so it can be
run on any day to check the report looks right.

Run from the lambda/ directory:
    python send_weekly_email_report.py            # send it
    python send_weekly_email_report.py --dry-run  # print the HTML instead
"""

import argparse
import logging

from lambda_helpers.weekly_email_report import WeeklyEmailReport

logging.basicConfig(level=logging.INFO)


def run(dry_run=False):
    report = WeeklyEmailReport()

    if dry_run:
        body_html, email_count = report.build_current_report()
        print(body_html)
        print(f"\n--- {email_count} emails in the last 7 days ---")
        return

    # week_key is omitted on purpose: a manual send should not consume the
    # marker that stops the real Sunday run from sending its report.
    email_count = report.send_report()
    print(f"Sent report covering {email_count} emails — check your inbox.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the report HTML to stdout instead of emailing it",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)
