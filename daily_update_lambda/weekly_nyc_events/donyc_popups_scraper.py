import re
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from daily_update_helpers.daily_update_constants import (
    DONYC_BASE_URL,
    DONYC_POPUPS_URL,
    POPUP_EVENT_LOOKAHEAD_DAYS,
)

logger = logging.getLogger(__name__)


class DonycPopupsScraper:
    """Fetches DoNYC's curated NYC pop-ups list via its JSON endpoint.

    DoNYC runs on the DoStuff network, where any listing page also serves JSON
    if you append ``.json``. The pop-ups page is already curated to pop-up
    events, so we just normalize fields and apply a near-term date window.

    Returns a list of normalized event dicts (not HTML); the combining step
    (PopupDessertScraper) merges/dedupes these with other sources via an LLM.
    """

    source = "DoNYC"
    MAX_EVENTS = 30

    def __init__(self):
        self.json_url = DONYC_POPUPS_URL + ".json"

    def fetch_events(self):
        logger.info("Fetching DoNYC pop-ups JSON")
        try:
            resp = requests.get(
                self.json_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Error fetching DoNYC pop-ups: %s", str(e), exc_info=True)
            return []

        today = datetime.now(ZoneInfo("America/New_York")).date()
        window_end = today + timedelta(days=POPUP_EVENT_LOOKAHEAD_DAYS)

        events = []
        for group in data.get("event_groups", []):
            for ev in group.get("events", []):
                normalized = self._normalize(ev)
                if not normalized:
                    continue
                if self._in_window(ev, today, window_end):
                    events.append(normalized)

        logger.info("DoNYC: %d pop-up events in window", len(events))
        return events[: self.MAX_EVENTS]

    def _normalize(self, ev):
        title = (ev.get("title") or "").strip()
        if not title:
            return None

        venue = ev.get("venue") or {}
        location = (venue.get("title") or "").strip() or "NYC"

        permalink = ev.get("permalink") or ""
        link = DONYC_BASE_URL + permalink if permalink.startswith("/") else permalink

        return {
            "title": title,
            "description": self._description(ev),
            "datetime": self._format_datetime(ev),
            "location": location,
            "link": link,
        }

    def _description(self, ev):
        # excerpt repeats the title on the first line; drop it, then trim.
        excerpt = (ev.get("excerpt") or ev.get("description") or "").strip()
        excerpt = re.sub(r"<[^>]+>", " ", excerpt)
        lines = [l.strip() for l in excerpt.splitlines() if l.strip()]
        if lines and lines[0].lower() == (ev.get("title") or "").strip().lower():
            lines = lines[1:]
        text = re.sub(r"\s+", " ", " ".join(lines)).strip()
        return text[:400]

    def _format_datetime(self, ev):
        begin = self._parse(ev.get("begin_time")) or self._parse(ev.get("begin_date"))
        if not begin:
            return ""
        begin_date = ev.get("begin_date") or ""
        end_date = ev.get("end_date") or ""
        # Multi-day pop-up: show the run as a date range.
        if end_date and end_date != begin_date:
            end = self._parse(end_date)
            if end:
                return f"{begin.strftime('%a, %b %-d')} – {end.strftime('%b %-d')}"
        # Single day: include the time if we have one.
        if "T" in (ev.get("begin_time") or ""):
            return begin.strftime("%a, %b %-d · %-I:%M %p")
        return begin.strftime("%a, %b %-d")

    def _in_window(self, ev, today, window_end):
        begin = self._parse(ev.get("begin_date"))
        end = self._parse(ev.get("end_date")) or begin
        if not begin:
            return False
        begin_d, end_d = begin.date(), end.date()
        # Keep events not yet ended that start within the lookahead window.
        return end_d >= today and begin_d <= window_end

    @staticmethod
    def _parse(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
