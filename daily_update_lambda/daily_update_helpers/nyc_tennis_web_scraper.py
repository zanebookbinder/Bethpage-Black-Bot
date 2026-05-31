"""Selenium scraper for NYC Parks tennis court availability."""

import logging
from datetime import datetime

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from daily_update_helpers.chrome_helper import create_headless_chrome_driver

logger = logging.getLogger(__name__)

AVAILABILITY_URL = "https://www.nycgovparks.org/tennisreservation/availability/12"
_DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class NycTennisWebScraper:
    def __init__(self):
        self.driver, self.wait = create_headless_chrome_driver(wait_seconds=15)

    def scrape_weekend_reservations(self):
        """
        Returns a list of (date_obj, date_label, {time_label: [url, ...]}) tuples
        sorted by date ascending, covering only Saturday/Sunday dates with availability.

        The page pre-loads all date schedules as Bootstrap tab-panes — no navigation needed.
        """
        self.driver.get(AVAILABILITY_URL)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        results = []
        for pane in soup.find_all(class_="tab-pane"):
            date_obj, date_label = self._parse_date_heading(pane)
            if not date_obj:
                continue

            # weekday(): 5=Saturday, 6=Sunday
            if date_obj.weekday() not in (5, 6):
                continue

            time_slots = self._parse_availability(pane)
            if not time_slots:
                continue

            logger.info("Found %r with %d available time slot(s)", date_label, len(time_slots))
            results.append((date_obj, date_label, time_slots))

        results.sort(key=lambda x: x[0])
        logger.info("Scraped %d weekend dates with availability", len(results))
        return results

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Parse helpers
    # ------------------------------------------------------------------

    def _parse_date_heading(self, soup):
        """Parse a date heading from a BS4 element. Returns (datetime, label) or (None, None)."""
        for tag in ["h1", "h2", "h3", "h4"]:
            for el in soup.find_all(tag):
                text = el.get_text(strip=True)
                if any(day in text for day in _DAYS_OF_WEEK):
                    for fmt in ["%A, %B %d, %Y", "%B %d, %Y"]:
                        try:
                            d = datetime.strptime(text, fmt)
                            return d, d.strftime("%A, %B %-d, %Y")
                        except ValueError:
                            pass
        return None, None

    def _parse_availability(self, soup):
        """
        Parse court availability from a BS4 element (typically a tab-pane).
        Returns {time_label: [reservation_url, ...]} for slots with at least one link.
        """
        time_slots = {}
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            header_cells = rows[0].find_all(["th", "td"])
            if not any("Court" in c.get_text() for c in header_cells):
                continue

            for row in rows[1:]:
                cells = row.find_all("td")
                if not cells:
                    continue
                time_label = cells[0].get_text(strip=True)
                if not time_label:
                    continue

                reservation_links = [
                    "https://www.nycgovparks.org" + a["href"]
                    if a["href"].startswith("/") else a["href"]
                    for cell in cells[1:]
                    for a in cell.find_all("a")
                    if "reserve" in a.get("href", "").lower()
                ]
                if reservation_links:
                    time_slots[time_label] = reservation_links

        return time_slots
