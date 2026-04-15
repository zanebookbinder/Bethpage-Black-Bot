"""Selenium scraper for NYC Parks tennis court availability."""

import logging
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from daily_update_helpers.chrome_helper import create_headless_chrome_driver

logger = logging.getLogger(__name__)

AVAILABILITY_URL = "https://www.nycgovparks.org/tennisreservation/availability/12"
_DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


class NycTennisWebScraper:
    """
    Scrapes the NYC Parks tennis reservation calendar for a single facility.
    Clicks each available weekend date and collects reservation links per time slot.
    """

    def __init__(self):
        self.driver, self.wait = create_headless_chrome_driver(wait_seconds=15)

    def scrape_weekend_reservations(self):
        """
        Returns a list of (date_obj, date_label, {time_label: [url, ...]}) tuples
        sorted by date ascending, covering only Saturday/Sunday dates.
        """
        self.driver.get(AVAILABILITY_URL)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

        positions = self._collect_weekend_positions()
        logger.info("Found %d available weekend dates to visit", len(positions))

        results = []
        for i, pos in enumerate(positions, 1):
            old_heading = self._get_schedule_heading_text()
            logger.info(
                "[%d/%d] Clicking date at table=%d row=%d col=%d (current heading: %r)",
                i, len(positions), pos["table_idx"], pos["row_idx"], pos["col_idx"], old_heading,
            )

            if not self._click_date_at_position(pos):
                continue

            try:
                self.wait.until(lambda d: self._get_schedule_heading_text() != old_heading)
            except TimeoutException:
                logger.warning(
                    "[%d/%d] Heading did not change after clicking position %s",
                    i, len(positions), pos,
                )

            date_obj, date_label = self._parse_selected_date_heading()
            time_slots = self._parse_availability_table()

            logger.info(
                "[%d/%d] Scraped %r — found %d available time slot(s)",
                i, len(positions), date_label, len(time_slots),
            )

            if time_slots and date_label:
                results.append((date_obj, date_label, time_slots))

        results.sort(key=lambda x: x[0] or datetime.max)
        return results

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Calendar helpers
    # ------------------------------------------------------------------

    def _collect_weekend_positions(self):
        """
        Walk every calendar table (S M T W T F S header) and record
        (table_idx, row_idx, col_idx) for each linked Saturday/Sunday cell.
        col 0 = Sunday, col 6 = Saturday.
        """
        positions = []
        calendar_table_idx = 0
        for table in self.driver.find_elements(By.CSS_SELECTOR, "table"):
            if not self._is_calendar_table(table):
                continue
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row_idx, row in enumerate(rows):
                cells = row.find_elements(By.TAG_NAME, "td")
                for col_idx in [0, 6]:
                    if col_idx >= len(cells):
                        continue
                    anchors = cells[col_idx].find_elements(By.TAG_NAME, "a")
                    if anchors:
                        day_text = anchors[0].text.strip()
                        logger.info(
                            "Found available weekend date: table=%d row=%d col=%d day=%r",
                            calendar_table_idx, row_idx, col_idx, day_text,
                        )
                        positions.append({
                            "table_idx": calendar_table_idx,
                            "row_idx": row_idx,
                            "col_idx": col_idx,
                        })
            calendar_table_idx += 1
        return positions

    def _click_date_at_position(self, pos):
        """Re-find the calendar link at (table_idx, row_idx, col_idx) and click it."""
        try:
            calendar_tables = [
                t for t in self.driver.find_elements(By.CSS_SELECTOR, "table")
                if self._is_calendar_table(t)
            ]
            table = calendar_tables[pos["table_idx"]]
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            cells = rows[pos["row_idx"]].find_elements(By.TAG_NAME, "td")
            anchor = cells[pos["col_idx"]].find_element(By.TAG_NAME, "a")
            self.driver.execute_script("arguments[0].click();", anchor)
            return True
        except Exception as e:
            logger.warning("Could not click date at position %s: %s", pos, e)
            return False

    def _is_calendar_table(self, table):
        """Return True if this table has the S M T W T F S day-of-week header."""
        th_elements = table.find_elements(By.TAG_NAME, "th")
        return [th.text.strip() for th in th_elements] == ["S", "M", "T", "W", "T", "F", "S"]

    # ------------------------------------------------------------------
    # Schedule helpers
    # ------------------------------------------------------------------

    def _get_schedule_heading_text(self):
        """Return the text of the heading that contains a day-of-week name, or None."""
        for tag in ["h1", "h2", "h3", "h4"]:
            for el in self.driver.find_elements(By.TAG_NAME, tag):
                text = el.text.strip()
                if any(day in text for day in _DAYS_OF_WEEK):
                    return text
        return None

    def _parse_selected_date_heading(self):
        """
        Parse the schedule heading into a (datetime, label) pair.
        Returns (None, None) if no parseable heading is found.
        """
        text = self._get_schedule_heading_text()
        if not text:
            logger.warning("No date heading found on %s", self.driver.current_url)
            return None, None

        for fmt in ["%A, %B %d, %Y", "%B %d, %Y"]:
            try:
                d = datetime.strptime(text, fmt)
                return d, d.strftime("%A, %B %-d, %Y")
            except ValueError:
                pass

        logger.warning("Could not parse date heading: %r", text)
        return None, None

    def _parse_availability_table(self):
        """
        Parse the court availability grid on the currently displayed date.
        Returns {time_label: [reservation_url, ...]} for slots with at least one
        "Reserve this time" link.
        """
        time_slots = {}
        for table in self.driver.find_elements(By.CSS_SELECTOR, "table"):
            if self._is_calendar_table(table):
                continue
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) < 2:
                continue

            header_cells = (
                rows[0].find_elements(By.TAG_NAME, "th")
                or rows[0].find_elements(By.TAG_NAME, "td")
            )
            if not any("Court" in c.text for c in header_cells):
                continue

            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue
                time_label = cells[0].text.strip()
                if not time_label:
                    continue

                reservation_links = []
                for cell in cells[1:]:
                    for anchor in cell.find_elements(By.TAG_NAME, "a"):
                        href = anchor.get_attribute("href") or ""
                        if "reservecp" in href or "reserve" in href.lower():
                            reservation_links.append(href)

                if reservation_links:
                    time_slots[time_label] = reservation_links

        return time_slots
