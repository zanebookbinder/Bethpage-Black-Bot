from zoneinfo import ZoneInfo

import boto3
import json
import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BUCKET = "daily-update-bot-data"
MAX_ENTRIES_PER_FILE = 1000


class S3DataService:
    """Generic append-only S3 service. Each data type writes to its own
    numbered file sequence, e.g. daily-health-data-1.json, daily-health-data-2.json."""

    def __init__(self, file_prefix: str):
        self.file_prefix = file_prefix
        self.s3 = boto3.client("s3", region_name="us-east-1")

    def _list_file_numbers(self):
        try:
            response = self.s3.list_objects_v2(Bucket=BUCKET, Prefix=self.file_prefix)
            numbers = []
            for obj in response.get("Contents", []):
                match = re.search(rf"{re.escape(self.file_prefix)}-(\d+)\.json", obj["Key"])
                if match:
                    numbers.append(int(match.group(1)))
            return sorted(numbers)
        except Exception as e:
            logger.error("Error listing S3 files: %s", str(e))
            return []

    def _read_file(self, number):
        key = f"{self.file_prefix}-{number}.json"
        try:
            response = self.s3.get_object(Bucket=BUCKET, Key=key)
            return json.loads(response["Body"].read().decode("utf-8"))
        except Exception as e:
            logger.error("Error reading S3 file %s: %s", key, str(e))
            return []

    def _write_file(self, number, entries):
        key = f"{self.file_prefix}-{number}.json"
        self.s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(entries, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        logger.info("Wrote %d entries to %s", len(entries), key)

    def upsert_entry_by_date(self, entry: dict) -> int:
        """Update an existing entry matching entry['date'], or append if not found.
        Rotates to a new file at 1,000 entries. Returns the file number written to."""
        if not entry.get("timestamp"):
            entry["timestamp"] = datetime.now(ZoneInfo("America/New_York"))

        date = entry.get("date")
        numbers = self._list_file_numbers()

        # Search all files for an existing entry with the same date
        if date:
            for number in reversed(numbers):
                entries = self._read_file(number)
                for i, existing in enumerate(entries):
                    if existing.get("date") == date:
                        entries[i] = entry
                        self._write_file(number, entries)
                        logger.info("Overwrote entry for date %s in %s-%d.json", date, self.file_prefix, number)
                        return number

        # Not found — append with rotation
        if not numbers:
            current_number = 1
            entries = []
        else:
            current_number = numbers[-1]
            entries = self._read_file(current_number)

        if len(entries) >= MAX_ENTRIES_PER_FILE:
            current_number += 1
            entries = []
            logger.info("Rotating to %s-%d.json", self.file_prefix, current_number)

        entries.append(entry)
        self._write_file(current_number, entries)
        return current_number
