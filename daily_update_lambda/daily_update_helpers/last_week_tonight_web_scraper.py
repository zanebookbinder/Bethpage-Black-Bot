"""Scraper for lastweektickets.com (Last Week Tonight with John Oliver free tickets).

The site is plain server-rendered HTML (no JS rendering required), so this uses
requests/BeautifulSoup rather than Selenium. The schedule lives in a
`<ul id="main_sched">` list; each `<li class="sched_line ...">` represents one
taping date, with modifier classes signaling status:
  - "no_more_tix"  -> sold out (excluded from results)
  - "sl_notyet"    -> tickets not yet released; the "sl_showtime" span holds the
                       release date/time instead of a showtime
  - (no modifier)  -> tickets currently available to request
"""

import logging
import time

import requests
from bs4 import BeautifulSoup

from daily_update_helpers.daily_update_constants import LAST_WEEK_TONIGHT_URL

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2

SCHEDULE_LIST_ID = "main_sched"
SOLD_OUT_CLASS = "no_more_tix"
NOT_YET_RELEASED_CLASS = "sl_notyet"


class TicketStatus:
    AVAILABLE = "Available"
    NOT_YET_RELEASED = "Not Yet Released"


class LastWeekTonightEntry:
    def __init__(self, date_text, status, detail):
        self.date_text = date_text
        self.status = status
        self.detail = detail

    def __str__(self):
        return f"[Last Week Tonight: {self.date_text} - {self.status} ({self.detail})]"

    def to_dict(self):
        return {
            "date_text": self.date_text,
            "status": self.status,
            "detail": self.detail,
        }


class LastWeekTonightWebScraper:
    def __init__(self):
        self.url = LAST_WEEK_TONIGHT_URL
        self.session = requests.Session()

    def find_available_and_upcoming_tapings(self):
        """
        Returns a list of LastWeekTonightEntry for dates where requesting tickets
        is currently possible, or where tickets have not been released yet.
        Sold-out dates are excluded. Returns [] on any scraping/parsing failure
        so callers can safely skip this section without failing the whole email.
        """
        html = self._fetch_html_with_retries()
        if html is None:
            return []

        try:
            return self._parse_schedule(html)
        except Exception as e:
            logger.error(
                "Error parsing Last Week Tonight schedule: %s", str(e), exc_info=True
            )
            return []

    def _fetch_html_with_retries(self):
        last_exception = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self.session.get(self.url, timeout=REQUEST_TIMEOUT_SECONDS)
                response.raise_for_status()
                return response.text
            except Exception as e:
                last_exception = e
                logger.warning(
                    "Attempt %d/%d to fetch %s failed: %s",
                    attempt,
                    MAX_ATTEMPTS,
                    self.url,
                    str(e),
                )
                if attempt < MAX_ATTEMPTS:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        logger.error(
            "Failed to fetch Last Week Tonight schedule after %d attempts: %s",
            MAX_ATTEMPTS,
            str(last_exception),
            exc_info=True,
        )
        return None

    def _parse_schedule(self, html):
        soup = BeautifulSoup(html, "html.parser")
        schedule_list = soup.find("ul", id=SCHEDULE_LIST_ID)
        if not schedule_list:
            logger.warning(
                "Could not find #%s on Last Week Tonight page; page layout may have changed",
                SCHEDULE_LIST_ID,
            )
            return []

        entries = []
        for li in schedule_list.find_all("li", class_="sched_line"):
            try:
                entry = self._parse_schedule_line(li)
                if entry:
                    entries.append(entry)
            except Exception as e:
                logger.warning(
                    "Skipping malformed Last Week Tonight schedule line: %s", str(e)
                )
                continue

        return entries

    def _parse_schedule_line(self, li):
        classes = li.get("class", [])

        if SOLD_OUT_CLASS in classes:
            return None

        day = li.find("span", class_="sl_day")
        date_num = li.find("span", class_="sl_date")
        month_year = li.find("span", class_="sl_my")
        showtime = li.find("span", class_="sl_showtime")

        if not (day and date_num and month_year):
            logger.warning(
                "Skipping schedule line missing expected date fields: %s", li
            )
            return None

        date_text = " ".join(
            [
                day.get_text(strip=True),
                date_num.get_text(strip=True),
                month_year.get_text(strip=True),
            ]
        )
        detail_text = showtime.get_text(strip=True) if showtime else ""

        status = (
            TicketStatus.NOT_YET_RELEASED
            if NOT_YET_RELEASED_CLASS in classes
            else TicketStatus.AVAILABLE
        )

        return LastWeekTonightEntry(date_text, status, detail_text)

    def close(self):
        try:
            self.session.close()
        except Exception as e:
            logger.debug("Error closing Last Week Tonight session: %s", str(e))
