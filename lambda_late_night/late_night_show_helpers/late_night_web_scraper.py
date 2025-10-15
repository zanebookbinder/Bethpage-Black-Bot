from os import wait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time


class WaitlistEntry:
    def __init__(self, date, show_name, button_text, show_time=None):
        self.date = date
        self.show_name = show_name
        self.button_text = button_text
        self.show_time = show_time

    def __str__(self):
        return f"[{self.show_name}: {self.date} at {self.show_time}]"

    def to_dynamo_db_item(self):
        return {'Date': self.date, 'Time': self.show_time, 'ButtonText': self.button_text}

    def from_dynamo_db_item(show_name, db_json):
        return WaitlistEntry(db_json['Date'], show_name, db_json['ButtonText'], db_json['Time'])


BASE_URL = "https://1iota.com/"
COLBERT_URL = "https://1iota.com/show/536/the-late-show-with-stephen-colbert"
SETH_MEYERS_URL = "https://1iota.com/show/461/late-night-with-seth-meyers"
DAILY_SHOW_URL = "https://1iota.com/show/1248/the-daily-show"
FALLON_URL = "https://1iota.com/show/353/the-tonight-show-starring-jimmy-fallon"
URL_TO_SHOW_NAME_DICT = {
    COLBERT_URL: "The Late Show with Stephen Colbert",
    SETH_MEYERS_URL: "Late Night with Seth Meyers",
    DAILY_SHOW_URL: "The Daily Show",
    FALLON_URL: "The Tonight Show Starring Jimmy Fallon"
}

class LateNightWebScraper:

    def __init__(self):
        self.base_url = BASE_URL

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--remote-debugging-pipe")
        chrome_options.add_argument("--log-path=/tmp")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )

        try:
            service = Service(service_log_path="/tmp/chromedriver.log")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

            service = Service(
                executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
                service_log_path="/tmp/chromedriver.log",
            )

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)
        self.wait_short = WebDriverWait(self.driver, 0.5)

    def find_all_available_waitlists(self):
        """
        Scrapes 1iota.com for late night show tickets.
        Returns a list of dictionaries containing date and URL for shows with 'Join Waitlist' buttons.
        """
        waitlist_entries = {}  # (show_url: list of waitlist entries)

        print(
            f"Checking {len(URL_TO_SHOW_NAME_DICT.keys())} late night shows for waitlist opportunities"
        )

        # Visit each show page directly and check for waitlist opportunities
        for show_url, show_name in URL_TO_SHOW_NAME_DICT.items():
            try:
                print(f"Checking show: {show_name}")
                waitlist_entries[show_name] = self.find_available_waitlists_for_show(
                    show_url
                )
                print(
                    f"Found {len(waitlist_entries[show_name])} waitlist opportunities for this show"
                )
            except Exception as e:
                print(f"Error processing show {show_name} {show_url}: {e}")
                raise e

        return waitlist_entries

    def find_available_waitlists_for_show(self, show_url):
        """
        Check a specific show page for waitlist opportunities.
        Returns a list of dictionaries with date and URL for waitlist entries.
        """
        waitlist_entries = []

        self.driver.get(show_url)

        calendar_dates, calendar_icon_div = self.find_show_dates()
        if not calendar_dates:
            print(f"No calendar dates found for {show_url}")
            return waitlist_entries

        calendar_dates_list = [
            (self.get_date_text_from_date_element(date), date)
            for date in calendar_dates
        ]
        calendar_dates_list_not_null = [
            (k, v) for k, v in calendar_dates_list if (v is not None and k is not None)
        ]
        print(
            f"Non-null calendar dates: {', '.join([k for k, v in calendar_dates_list_not_null])}"
        )

        # Track already checked dates to avoid repeats
        checked_dates = set()
        i = 0
        should_click_calendar = False

        while True:

            if i < len(calendar_dates_list_not_null):
                try:
                    date_text, date_element = calendar_dates_list_not_null[i]

                    # Parse the date
                    if date_text in checked_dates:
                        print(f"Date {date_text} already checked, skipping")
                        i += 1
                        continue

                    # Add to checked dates
                    checked_dates.add(date_text)

                    # Check if date is sold out
                    if self.date_is_sold_out(date_text):
                        i += 1
                        continue

                    self.click_date_and_screenshot(
                        date_element, date_text, should_screenshot=False
                    )

                    # Check for waitlist opportunity
                    waitlist_entry = self.check_for_waitlist(date_text, show_url)
                    if waitlist_entry:
                        waitlist_entries.append(waitlist_entry)

                    i += 1

                except StaleElementReferenceException as sere:
                    should_click_calendar = True

            # look for more dates
            if should_click_calendar or i == len(calendar_dates_list_not_null):
                if calendar_icon_div:
                    try:
                        calendar_icon_div.click()
                    except Exception as e:
                        print(f"Error clicking on the first calendar icon div: {e}")
                calendar_dates, calendar_icon_div = self.find_show_dates()
                calendar_dates_list = [
                    (self.get_date_text_from_date_element(date), date)
                    for date in calendar_dates
                ]

                new_calendar_dates_list = [
                    c
                    for c in calendar_dates_list
                    if c[0] not in checked_dates and c[0] is not None
                ]
                if not calendar_dates or not new_calendar_dates_list:
                    return waitlist_entries

                calendar_dates_list_not_null = new_calendar_dates_list
                i = 0

    def get_date_text_from_date_element(self, date_element):
        """
        Extract date text from a date element (now directly a dayDiv).
        Returns the date text or None if the element doesn't have date structure.
        """
        try:
            # Since we're now selecting div.dayDiv directly, date_element IS the dayDiv
            month_div = date_element.find_element(By.CSS_SELECTOR, "div.month")
            dom_div = date_element.find_element(By.CSS_SELECTOR, "div.dom")
            dow_div = date_element.find_element(By.CSS_SELECTOR, "div.dow")

            month = month_div.text.strip()
            day = dom_div.text.strip()
            day_of_week = dow_div.text.strip()

            # Format as "Mon Sep 22" to match your desired format
            date_text = f"{day_of_week} {month} {day}"
            return date_text.replace("\n", "")
        except NoSuchElementException:
            # This element doesn't have the expected date structure
            return None

    def date_is_sold_out(self, date_text):
        """
        Check if the date is sold out and skip if so.
        Returns True if sold out, False otherwise.
        """
        if "SOLD OUT" in date_text:
            print(f"Date {date_text.replace('SOLD OUT', '')} is sold out, skipping")
            return True
        return False

    def click_date_and_screenshot(
        self, date_element, date_text, should_screenshot=False
    ):
        """
        Click the date element and take a screenshot.
        """
        # Click the parent li element instead of the dayDiv
        parent_li = date_element.find_element(By.XPATH, "./..")
        self.driver.execute_script("arguments[0].click();", parent_li)
        time.sleep(0.25)

        if should_screenshot:
            # Take a screenshot after clicking the date
            try:
                screenshot_filename = f"screenshot_{date_text.replace(' ', '_')}.png"
                self.driver.save_screenshot(screenshot_filename)
                print(f"Screenshot saved: {screenshot_filename}")
            except Exception as screenshot_exc:
                print(f"Failed to take screenshot for {date_text}: {screenshot_exc}")

    def check_for_waitlist(self, date_text, show_url):
        """
        Check if there's a waitlist opportunity for the current date.
        Returns waitlist entry dict if found, None otherwise.
        """
        try:
            # Wait for the button to appear (timeout after 3 seconds)
            button = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'eventList')]//button[contains(@class, 'btn-action')]",
                    )
                )
            )
            button_text = button.text.strip()

            # Try to grab the show time
            try:
                time_element = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class, 'eventDetailSection')]//div[contains(@class, 'fa-clock')]/parent::div"
                )
                show_time = time_element.text.strip()
            except Exception:
                show_time = None  # fallback if no time is found

            if "join waitlist" in button_text.lower():
                waitlist_entry = WaitlistEntry(date_text, URL_TO_SHOW_NAME_DICT[show_url], button_text, show_time)
                return waitlist_entry
        except Exception as e:
            print(f"No waitlist button found for date {date_text}: {e}")

        return None

    def find_show_dates(self):
        """
        Find all clickable calendar dates under the Ticket Calendar section.
        Returns a list of date elements.
        """
        try:
            # Look for the tabList containing calendar dates
            # Based on the HTML structure: <ul class="tabList"> with <li class="tabWidth">
            date_tabs = self.wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "(//ul[contains(@class, 'tabList')])[1]//li[contains(@class, 'tabWidth')]//div[contains(@class, 'dayDiv') and not(@id='dayDivCalendar')]",
                    )
                )
            )

            # Now look for the special calendar icon div within an li in the ul that has the dayDivCalendar id
            calendar_icon_divs = self.driver.find_elements(
                By.XPATH,
                "//ul[contains(@class, 'tabList')]//li//div[@id='dayDivCalendar']",
            )

            print(f"Found {len(date_tabs)} date tabs")
            print(
                f"Found {len(calendar_icon_divs)} calendar icon divs with id='dayDivCalendar'"
            )
            return date_tabs, calendar_icon_divs[0] if calendar_icon_divs else None

        except Exception as e:
            print(f"Error finding calendar dates: {e}")
            raise e

    def _find_main_button(self):
        """
        Find the main action button on the page (likely for tickets/waitlist).
        Returns the button element or None if not found.
        """
        try:
            # Look for buttons with common waitlist/ticket text
            button_texts = [
                "Join Waitlist",
                "Get Tickets",
                "Request Tickets",
                "Register",
                "Sign Up",
            ]

            for text in button_texts:
                try:
                    button = self.driver.find_element(
                        By.XPATH, f"//button[contains(text(), '{text}')]"
                    )
                    if button and button.is_displayed():
                        return button
                except NoSuchElementException:
                    continue

            # Look for the most prominent button (usually the largest or most styled)
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            if buttons:
                # Return the first visible button as fallback
                for button in buttons:
                    if button.is_displayed() and button.text.strip():
                        return button

        except Exception as e:
            print(f"Error finding main button: {e}")

        return None

    def close(self):
        self.driver.quit()
