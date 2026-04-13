import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from s3_data_service import S3DataService

logger = logging.getLogger(__name__)

FILE_PREFIX = "daily-health-data"


def handle(body: dict) -> tuple[int, dict]:
    """Store health data for 'today' or 'yesterday' based on the 'day' parameter.
    Upserts by date. Returns (status_code, response_body)."""
    day = body.get("day")
    if day not in ("today", "yesterday"):
        return 400, {"error": "'day' must be 'today' or 'yesterday'"}

    steps = body.get("steps")
    if steps is None:
        return 400, {"error": "'steps' is required"}

    now = datetime.now(ZoneInfo("America/New_York"))
    dt = now if day == "today" else now - timedelta(days=1)

    entry = {
        "date": dt.strftime("%d/%m/%Y"),
        "timestamp": now.isoformat(),
        "steps": steps,
        "walking_distance_miles": body.get("walking_distance_miles"),
    }

    service = S3DataService(FILE_PREFIX)
    file_number = service.upsert_entry_by_date(entry)
    logger.info("Upserted %s health data (%s) into %s-%d.json", day, entry["date"], FILE_PREFIX, file_number)

    return 200, {"message": "Health data recorded", "date": entry["date"], "file": f"{FILE_PREFIX}-{file_number}.json"}
