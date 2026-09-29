import json
import time
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from daily_update_helpers.chrome_helper import create_headless_chrome_driver
from daily_update_helpers.daily_update_constants import NEW_YORK_CARES_BASE_URL
from daily_update_helpers.travel_time_calculation_service import (
    TravelTimeCalculationService,
)

# Each card has up to 3 of these icon rows: site name, date/time, borough.
ICON_ROW_SELECTOR = "div.flex.flex-start.items-center.my-10.gap-3"
PROJECT_CARD_SELECTOR = 'div[class*="project-card-default"]'
MAX_STALE_RETRIES = 3


class NewYorkCaresWebScraper:
    """Scraper for New York Cares project cards (`project-card-default`).
    Prefers a legacy JSON payload in a child `<div class="hidden">` if present,
    otherwise parses the visible card markup directly. Returns dicts with
    `title`, `date`, `time`, `location`, `link`, `description`."""

    def __init__(self, url: str = None):
        self.url = url or NEW_YORK_CARES_BASE_URL
        self.driver, self.wait = create_headless_chrome_driver(wait_seconds=10)
        self.travel_time_service = TravelTimeCalculationService()

    def find_weekend_opportunities(self) -> List[dict]:
        """Render the page with Selenium and extract opportunity details.

        DOM extraction happens in one pass (with stale-element retries) before
        the driver is closed, then the slow, sequential travel-time API calls
        run afterward with no Selenium involved. Mixing those two phases
        previously caused most cards to fail with "stale element reference"
        once travel-time lookups added enough delay for the page's
        post-hydration re-render to invalidate the earlier element handles.
        """
        print("Scraping New York Cares for weekend volunteering opportunities...")

        entries = self._extract_all_card_entries()
        results = self._attach_travel_times(entries)

        print("Found", len(results), "New York Cares opportunities.")
        return results

    def _extract_all_card_entries(self) -> List[dict]:
        """Fast DOM-only pass: render the page and pull title/date/time/location
        (and link/description) out of every non-full project card. No network
        calls happen here, so element handles are only ever held briefly.

        The page still re-renders shortly after its first paint (hydration),
        which can invalidate element handles collected just before it happens
        regardless of how fast we read them. We wait for the card markup to
        stop changing before reading it, and on top of that retry any card
        that still goes stale by re-locating it fresh via its index.
        """
        entries = []
        try:
            self.driver.get(self.url)
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PROJECT_CARD_SELECTOR))
            )
            self._wait_for_page_to_stabilize()

            num_cards = len(
                self.driver.find_elements(By.CSS_SELECTOR, PROJECT_CARD_SELECTOR)
            )

            for index in range(num_cards):
                entry = self._extract_card_at_index_with_retry(index)
                if entry:
                    entries.append(entry)

        except Exception as e:
            print(f"Error rendering page or finding cards: {e}")
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

        return entries

    def _wait_for_page_to_stabilize(self, required_stable_checks=2, interval=0.4, timeout=6):
        """Poll the rendered page size until it stops changing (or timeout),
        to ride out client-side hydration/re-renders before we start reading
        card elements. Card *count* alone isn't a reliable signal here since
        hydration swaps content in place without changing how many cards
        exist, so we hash the full body markup instead.
        """
        deadline = time.time() + timeout
        last_length = None
        stable_checks = 0
        while time.time() < deadline:
            try:
                current_length = self.driver.execute_script(
                    "return document.body.innerHTML.length;"
                )
            except Exception:
                return
            if last_length is not None and current_length == last_length:
                stable_checks += 1
                if stable_checks >= required_stable_checks:
                    return
            else:
                stable_checks = 0
            last_length = current_length
            time.sleep(interval)

    def _extract_card_at_index_with_retry(self, index: int) -> Optional[dict]:
        """Re-locates the card at `index` fresh on each attempt (rather than
        reusing a possibly-stale handle) so a mid-loop re-render only costs a
        retry instead of silently dropping the card.
        """
        for attempt in range(1, MAX_STALE_RETRIES + 1):
            try:
                cards = self.driver.find_elements(
                    By.CSS_SELECTOR, PROJECT_CARD_SELECTOR
                )
                if index >= len(cards):
                    return None
                return self._extract_one_card(cards[index])
            except StaleElementReferenceException:
                if attempt == MAX_STALE_RETRIES:
                    print(f"Skipping card {index}: stale after {MAX_STALE_RETRIES} retries")
                    return None
                time.sleep(0.3)
                continue
            except Exception as e:
                print(f"Skipping card {index} due to error: {e}")
                return None

    def _extract_one_card(self, card) -> Optional[dict]:
        """Extract a single opportunity dict from a project card, or None if
        it's full or missing required fields. Raises StaleElementReferenceException
        to the caller so it can be retried rather than silently swallowed here.
        """
        hidden = None
        try:
            hidden = card.find_element(By.CSS_SELECTOR, "div.hidden")
        except NoSuchElementException:
            hidden = None

        data = None
        if hidden:
            raw = hidden.get_attribute("textContent") or hidden.text
            raw = raw.strip()
            try:
                data = json.loads(raw)
            except Exception:
                data = None

        if data:
            title = data.get("Public_Session_Name__c") or data.get("Name")
            date = data.get("Session_Start_Date__c")
            start_time = data.get("Session_Start_Time_Formatted__c")
            end_time = data.get("Session_End_Time_Formatted__c")
            if start_time and end_time:
                time_str = f"{start_time} - {end_time}"
            else:
                time_str = start_time or end_time
            location = data.get("Address__c") or data.get("Location_Address__tl")
            description = data.get("Description__c")
        else:
            # Site no longer embeds a JSON payload in a hidden div;
            # fall back to parsing the visible card markup directly.
            title, date, time_str, location, description = (
                self._extract_details_from_card_dom(card)
            )

        is_full = False
        if data:
            capacity = data.get("Capacity_Remaining__c")
            if capacity is not None and int(capacity) <= 0:
                is_full = True

        if not is_full:
            try:
                # visible "Project filled" button or similar indicator
                filled_btn = card.find_element(
                    By.CSS_SELECTOR,
                    "a.project-filled-button, a.btn-grey.project-filled-button",
                )
                btn_text = (filled_btn.text or "").strip().lower()
                if "filled" in btn_text:
                    is_full = True
            except NoSuchElementException:
                pass

        if is_full:
            return None

        link = None
        try:
            link_el = card.find_element(By.CSS_SELECTOR, 'a[href^="/project/"]')
            link = link_el.get_attribute("href")
        except NoSuchElementException:
            link = None

        if not title or not date or not time_str or not location:
            return None

        return {
            "title": title,
            "date": date,
            "time": time_str,
            "location": location,
            "link": link,
            "description": description,
        }

    def _attach_travel_times(self, entries: List[dict]) -> List[dict]:
        """Second pass: compute transit/walking time for each extracted entry.
        Pure network calls, no Selenium involved, so it's safe to take a while.
        """
        results = []
        for entry in entries:
            location = entry["location"]
            try:
                transit_time = self.travel_time_service.get_travel_time(
                    location, "transit"
                )
                walking_time = self.travel_time_service.get_travel_time(
                    location, "walking"
                )
            except Exception as e:
                print(f"Error computing travel time for {location!r}: {e}")
                transit_time = None
                walking_time = None

            results.append({**entry, "transit_time": transit_time, "walking_time": walking_time})

        return results

    def _extract_details_from_card_dom(self, card):
        """Extract title/date/time/location/description from the visible card
        markup. Each card has up to 3 icon rows (site name, date/time, borough);
        the date row is located by its <time> element rather than by position,
        since that's the only structurally reliable signal. Cards rendered for
        other breakpoints have 0 icon rows and naturally yield all-None here,
        which the caller skips via the existing missing-field check.
        """
        icon_rows = card.find_elements(By.CSS_SELECTOR, ICON_ROW_SELECTOR)

        date = None
        time_str = None
        date_row_index = None
        for idx, row in enumerate(icon_rows):
            time_els = row.find_elements(By.TAG_NAME, "time")
            if time_els:
                date_row_index = idx
                datetime_attr = time_els[0].get_attribute("datetime")
                if datetime_attr:
                    date = datetime_attr.split(" ")[0]
                time_str = " ".join(time_els[0].text.split())
                break

        other_rows = [
            row for idx, row in enumerate(icon_rows) if idx != date_row_index
        ]

        def _row_text(row):
            try:
                return row.find_element(By.TAG_NAME, "p").text.strip()
            except NoSuchElementException:
                return None

        site_name = _row_text(other_rows[0]) if len(other_rows) >= 1 else None
        borough = _row_text(other_rows[1]) if len(other_rows) >= 2 else None

        if site_name and borough:
            location = f"{site_name}, {borough}"
        else:
            location = site_name or borough

        try:
            title = card.find_element(By.TAG_NAME, "h2").text.strip()
        except NoSuchElementException:
            title = None

        try:
            description = card.find_element(By.CSS_SELECTOR, "div.mb-40 p").text.strip()
        except NoSuchElementException:
            description = None

        return title, date, time_str, location, description

    def format_time(self, hhmm: str) -> str:
        """Convert '08:30' -> '8:30AM', '12:30'->'12:30PM'. If input not in HH:MM, return original."""
        try:
            parts = hhmm.split(":")
            if len(parts) != 2:
                return hhmm
            h = int(parts[0])
            m = int(parts[1])
            suffix = "AM" if h < 12 else "PM"
            h_display = h if 1 <= h <= 12 else (h - 12 if h > 12 else 12)
            return f"{h_display}:{m:02d}{suffix}"
        except Exception:
            return hhmm


# n = NewYorkCaresWebScraper()
# o = n.find_weekend_opportunities()
# for a in o:
#     print(a)
#     print('\n\n')
# print(f"Found {len(o)} opportunities.")
