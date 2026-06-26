import re
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from daily_update_helpers.daily_update_constants import (
    NYC_FOR_FREE_BASE_URL,
    NYC_FOR_FREE_EVENTS_URL,
    POPUP_EVENT_LOOKAHEAD_DAYS,
)

logger = logging.getLogger(__name__)


class NycForFreeScraper:
    """Fetches free NYC events from nycforfree.co via Squarespace's JSON view.

    Squarespace serves any collection as JSON when ``?format=json`` is added.
    The ``upcoming`` array holds events with epoch-millis ``startDate`` and a
    structured ``location``. This source is broad (all free events), so the
    later LLM step filters down to pop-ups / food / dessert relevance.

    Returns normalized event dicts (not HTML) for the combining step.
    """

    source = "NYCforFree"
    MAX_EVENTS = 30

    def __init__(self):
        self.json_url = NYC_FOR_FREE_EVENTS_URL + "?format=json"

    def fetch_events(self):
        logger.info("Fetching NYCforFree events JSON")
        try:
            resp = requests.get(
                self.json_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Error fetching NYCforFree: %s", str(e), exc_info=True)
            return []

        today = datetime.now(ZoneInfo("America/New_York")).date()
        window_end = today + timedelta(days=POPUP_EVENT_LOOKAHEAD_DAYS)

        events = []
        for item in data.get("upcoming", []):
            normalized = self._normalize(item)
            if normalized and self._in_window(item, today, window_end):
                events.append(normalized)

        logger.info("NYCforFree: %d events in window", len(events))
        return events[: self.MAX_EVENTS]

    def _normalize(self, item):
        title = (item.get("title") or "").strip()
        if not title:
            return None

        full_url = item.get("fullUrl") or ""
        link = NYC_FOR_FREE_BASE_URL + full_url if full_url.startswith("/") else full_url

        return {
            "title": title,
            "description": self._description(item),
            "datetime": self._format_datetime(item),
            "location": self._location(item),
            "link": link,
        }

    def _description(self, item):
        raw = item.get("excerpt") or item.get("body") or ""
        # Squarespace bodies embed <style> blocks and #block-... CSS; strip them.
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["style", "script"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        text = re.sub(r"#block-[0-9a-f]+\s*\{[^}]*\}", " ", text)  # leftover inline CSS
        text = re.sub(r"\s+", " ", text).replace("\xa0", " ").strip()
        return text[:400]

    def _location(self, item):
        loc = item.get("location") or {}
        parts = [
            (loc.get("addressTitle") or "").strip(),
            (loc.get("addressLine1") or "").strip(),
            (loc.get("addressLine2") or "").strip(),
        ]
        location = ", ".join(p for p in parts if p)
        return location or "NYC"

    def _format_datetime(self, item):
        begin = self._parse(item.get("startDate"))
        if not begin:
            return ""
        end = self._parse(item.get("endDate"))
        if end and end.date() != begin.date():
            return f"{begin.strftime('%a, %b %-d')} – {end.strftime('%b %-d')}"
        return begin.strftime("%a, %b %-d")

    def _in_window(self, item, today, window_end):
        begin = self._parse(item.get("startDate"))
        end = self._parse(item.get("endDate")) or begin
        if not begin:
            return False
        return end.date() >= today and begin.date() <= window_end

    @staticmethod
    def _parse(epoch_ms):
        if not isinstance(epoch_ms, (int, float)):
            return None
        # Stored as midnight UTC representing the local event date.
        return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
