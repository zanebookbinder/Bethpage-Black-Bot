from zoneinfo import ZoneInfo

import boto3
import json
import re
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

BUCKET = "daily-update-bot-data"
FILE_PREFIX = "daily-health-data"


class HealthDataBot:
    def __init__(self):
        self.s3 = boto3.client("s3", region_name="us-east-1")

    def scrape_data_and_return_email_html(self):
        try:
            today = datetime.now(ZoneInfo("America/New_York"))
            target_date = today.strftime("%d/%m/%Y")

            entry = self._get_entry_by_date(target_date)
            if not entry:
                logger.info("No health data found for %s", target_date)
                return ""

            steps = entry.get("steps")
            distance = entry.get("walking_distance_miles")

            rows = ""
            if steps is not None:
                rows += f"<tr><td style='padding: 6px 12px;'>Steps</td><td style='padding: 6px 12px;'><strong>{int(steps):,}</strong></td></tr>"
            if distance is not None:
                rows += f"<tr><td style='padding: 6px 12px;'>Walking Distance</td><td style='padding: 6px 12px;'><strong>{float(distance):.2f} mi</strong></td></tr>"

            if not rows:
                return ""

            return f"""
            <h2>Today's Health Data ({target_date})</h2>
            <table style="border-collapse: collapse;">
                {rows}
            </table>
            """
        except Exception as e:
            logger.error("Error reading health data from S3: %s", str(e))
            return ""

    def _get_entry_by_date(self, date: str):
        """Search all files (newest first) for an entry matching the given DD/MM/YYYY date."""
        for number in reversed(self._list_file_numbers()):
            for entry in reversed(self._read_file(number)):
                if entry.get("date") == date:
                    return entry
        return None

    def _list_file_numbers(self):
        try:
            response = self.s3.list_objects_v2(Bucket=BUCKET, Prefix=FILE_PREFIX)
            numbers = []
            for obj in response.get("Contents", []):
                match = re.search(r"daily-health-data-(\d+)\.json", obj["Key"])
                if match:
                    numbers.append(int(match.group(1)))
            return sorted(numbers)
        except Exception as e:
            logger.error("Error listing S3 files: %s", str(e))
            return []

    def _read_file(self, number):
        key = f"{FILE_PREFIX}-{number}.json"
        try:
            response = self.s3.get_object(Bucket=BUCKET, Key=key)
            return json.loads(response["Body"].read().decode("utf-8"))
        except Exception as e:
            logger.error("Error reading S3 file %s: %s", key, str(e))
            return []
