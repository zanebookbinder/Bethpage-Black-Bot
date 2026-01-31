"""Web scraper for MyImpactPage / Better Impact volunteer opportunities."""

import re
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from daily_update_helpers.chrome_helper import create_headless_chrome_driver
from daily_update_helpers.daily_update_constants import (
    MYIMPACTPAGE_BASE_URL,
    MYIMPACTPAGE_LOGIN_URL,
    MYIMPACTPAGE_OPPORTUNITIES_URL,
    MYIMPACTPAGE_BAD_OPPORTUNITY_NAMES,
    MYIMPACTPAGE_NAVBAR_MARKERS,
    MAX_MYIMPACTPAGE_SHIFTS,
)


class MyImpactPageWebScraper:
    """Scrapes MyImpactPage for volunteer opportunities with space available."""

    def __init__(self):
        self.driver, self.wait = create_headless_chrome_driver(wait_seconds=15)

    def login(self, username: str, password: str) -> bool:
        """Log in to MyImpactPage. Returns True if successful."""
        try:
            self.driver.get(MYIMPACTPAGE_LOGIN_URL)
            time.sleep(2)  # Allow page to load

            # Try multiple selector strategies for username/password fields
            username_field = self._find_username_field()
            password_field = self._find_password_field()

            if not username_field or not password_field:
                print("Could not find login form fields")
                return False

            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            # Find and click login button
            login_btn = self._find_login_button()
            if login_btn:
                login_btn.click()
            else:
                # Try form submit
                password_field.submit()

            time.sleep(3)  # Wait for redirect after login

            # Check if we're still on login page (login failed)
            if (
                "Login" in self.driver.current_url
                and "Schedule" not in self.driver.current_url
            ):
                print("Login may have failed - still on login page")
                return False

            return True
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def _find_username_field(self):
        """Find username input using various strategies."""
        selectors = [
            (By.NAME, "Username"),
            (By.NAME, "username"),
            (By.ID, "Username"),
            (By.ID, "username"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[@placeholder='Username']"),
            (By.XPATH, "//input[contains(@name, 'ser')]"),
        ]
        return self._find_input(selectors)

    def _find_password_field(self):
        """Find password input using various strategies."""
        selectors = [
            (By.NAME, "Password"),
            (By.NAME, "password"),
            (By.ID, "Password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']"),
        ]
        return self._find_input(selectors)

    def _find_input(self, selectors):
        for by, value in selectors:
            try:
                elem = self.driver.find_element(by, value)
                if elem.is_displayed():
                    return elem
            except NoSuchElementException:
                continue
        return None

    def _find_login_button(self):
        """Find and return the login button."""
        selectors = [
            (By.XPATH, "//input[@type='submit' and contains(@value, 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(., 'Login')]"),
            (By.XPATH, "//input[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
        ]
        for by, value in selectors:
            try:
                elem = self.driver.find_element(by, value)
                if elem.is_displayed():
                    return elem
            except NoSuchElementException:
                continue
        return None

    def get_opportunities_with_space_available(self) -> list[dict]:
        """
        Parse the opportunities list, visit each link to check for shifts with space,
        and return only opportunities that have at least one available shift.
        """
        all_opportunities = []
        try:
            self.driver.get(MYIMPACTPAGE_OPPORTUNITIES_URL)
            time.sleep(3)  # Allow dynamic content to load

            # Step 1: Parse OpportunityHolder table to get list of links
            opportunity_links = self._parse_opportunities_list()

            opportunity_links = [
                opp
                for opp in opportunity_links
                if all(n not in opp["name"] for n in MYIMPACTPAGE_BAD_OPPORTUNITY_NAMES)
            ]

            print(f"Found {len(opportunity_links)} opportunities to check")

            # Step 2: Visit each link and extract shifts with availability
            for i, opp_link in enumerate(opportunity_links):
                try:
                    result = self._visit_opportunity_details(opp_link)
                    if result and (
                        "Saturday" in result[0].get("date", "")
                        or "Sunday" in result[0].get("date", "")
                    ):
                        all_opportunities.extend(result)
                        print(
                            f"  [{i + 1}/{len(opportunity_links)}] {opp_link['name']}: "
                            f"{len(result)} weekend shift(s) with space"
                        )
                except Exception as e:
                    print(f"  Error visiting {opp_link.get('name', 'unknown')}: {e}")
                time.sleep(1)  # Brief pause between requests

        except Exception as e:
            print(f"Error fetching opportunities: {e}")
        return all_opportunities[:MAX_MYIMPACTPAGE_SHIFTS]

    def _parse_opportunities_list(self) -> list[dict]:
        """
        Parse #OpportunityHolder table to get each opportunity's name and details link.
        Table structure: Activity (link) | info button | Shifts | Start Date | End Date
        """
        links = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "#OpportunityHolder table.fancy tbody tr",
            )
            for row in rows:
                try:
                    link_elem = row.find_element(By.CSS_SELECTOR, "td:first-child a")
                    href = link_elem.get_attribute("href")
                    name = link_elem.text.strip()
                    if not href or not name:
                        continue
                    if href.startswith("/"):
                        href = MYIMPACTPAGE_BASE_URL + href
                    links.append({"name": name, "url": href})
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            # Fallback: try generic table structure
            try:
                rows = self.driver.find_elements(
                    By.XPATH,
                    "//div[@id='OpportunityHolder']//table//tbody/tr",
                )
                for row in rows:
                    try:
                        link_elem = row.find_element(By.TAG_NAME, "a")
                        href = link_elem.get_attribute("href")
                        name = link_elem.text.strip()
                        if href and name and "OpportunityDetails" in href:
                            if href.startswith("/"):
                                href = MYIMPACTPAGE_BASE_URL + href
                            links.append({"name": name, "url": href})
                    except NoSuchElementException:
                        continue
            except NoSuchElementException:
                pass
        return links

    def _visit_opportunity_details(self, opp_link: dict) -> list[dict]:
        """
        Visit an opportunity's detail page and return list of shifts with space available.
        Each item: name, date, time, spaces, url (for sign up).
        """
        self.driver.get(opp_link["url"])
        time.sleep(2)  # Allow shifts table to load

        shifts = self._parse_shifts_on_detail_page(opp_link["name"], opp_link["url"])
        return shifts

    def _parse_shifts_on_detail_page(
        self, opportunity_name: str, opportunity_url: str
    ) -> list[dict]:
        """
        Parse the opportunity details page for shifts with space available.
        Table columns: Date, Start Time, End Time, Openings (e.g. "8 / 10"), Sign Up.
        Open Slots = first number from "X / Y" (spots remaining).
        Excludes navbar rows and Full rows.
        """

        def _extract_open_slots(text: str) -> str:
            """Extract spots remaining from 'X / Y' format. E.g. '8 / 10' -> '8'."""
            m = re.search(r"(\d+)\s*/\s*\d+", text or "")
            return m.group(1) if m else (text or "").strip()

        shifts = []
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in rows:
                try:
                    text = row.text
                    if not text.strip():
                        continue
                    if any(m in text for m in MYIMPACTPAGE_NAVBAR_MARKERS):
                        continue
                    # Skip rows that are clearly full
                    if "Full" in text or "0 space" in text.lower():
                        continue

                    # Check for Sign Up / Register link (indicates space available)
                    signup_links = row.find_elements(
                        By.XPATH,
                        ".//a[contains(translate(text(), 'SIGNUP', 'signup'), 'sign up') "
                        "or contains(translate(text(), 'REGISTER', 'register'), 'register')]",
                    )
                    signup_links.extend(
                        row.find_elements(
                            By.XPATH,
                            ".//button[contains(translate(text(), 'SIGNUP', 'signup'), 'sign up') "
                            "or contains(translate(text(), 'REGISTER', 'register'), 'register')]",
                        )
                    )

                    if signup_links:
                        shift_url = (
                            signup_links[0].get_attribute("href")
                            if signup_links[0].tag_name.lower() == "a"
                            else opportunity_url
                        )
                        if shift_url and shift_url.startswith("/"):
                            shift_url = MYIMPACTPAGE_BASE_URL + shift_url
                        if not shift_url:
                            shift_url = opportunity_url

                        cells = row.find_elements(By.TAG_NAME, "td")
                        parts = [c.text.strip() for c in cells]
                        # Typical columns: Date, Start Time, End Time, Openings (X / Y), ...
                        date = parts[0] if len(parts) > 0 else ""
                        start_time = parts[1] if len(parts) > 1 else ""
                        end_time = parts[2] if len(parts) > 2 else ""
                        open_slots_raw = parts[4] if len(parts) > 4 else ""
                        open_slots = _extract_open_slots(open_slots_raw)

                        shifts.append(
                            {
                                "name": opportunity_name,
                                "date": date,
                                "start_time": start_time,
                                "end_time": end_time,
                                "open_slots": open_slots,
                                "url": shift_url,
                            }
                        )
                except Exception:
                    continue
        except NoSuchElementException:
            pass

        # Fallback: rows that aren't Full or navbar
        if not shifts:
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                for row in rows:
                    text = row.text
                    if any(m in text for m in MYIMPACTPAGE_NAVBAR_MARKERS):
                        continue
                    if "Full" in text:
                        continue
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:
                        links = row.find_elements(By.TAG_NAME, "a")
                        shift_url = (
                            links[0].get_attribute("href") if links else opportunity_url
                        )
                        if shift_url and shift_url.startswith("/"):
                            shift_url = MYIMPACTPAGE_BASE_URL + shift_url
                        if not shift_url:
                            shift_url = opportunity_url
                        parts = [c.text.strip() for c in cells]
                        date = parts[0] if len(parts) > 0 else ""
                        start_time = parts[1] if len(parts) > 1 else ""
                        end_time = parts[2] if len(parts) > 2 else ""
                        open_slots = _extract_open_slots(
                            parts[4] if len(parts) > 4 else ""
                        )
                        shifts.append(
                            {
                                "name": opportunity_name,
                                "date": date,
                                "start_time": start_time,
                                "end_time": end_time,
                                "open_slots": open_slots,
                                "url": shift_url,
                            }
                        )
            except NoSuchElementException:
                pass

        return shifts

    def close(self):
        self.driver.quit()
