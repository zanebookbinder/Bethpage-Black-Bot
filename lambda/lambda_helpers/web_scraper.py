import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from lambda_helpers.date_handler import DateHandler
import time
import os

logger = logging.getLogger(__name__)

BETHPAGE_TEE_TIMES_WEBSITE_URL = 'https://foreupsoftware.com/index.php/booking/19765/2431#/teetimes'

# Configure which course(s) to search for (add more courses to the list if needed)
DESIRED_COURSES = ["Black"]  # e.g., ["Black", "Red"] to search multiple courses

class WebScraper:

    def __init__(self, username, password):
        # Ensure Selenium cache directory is writable in AWS Lambda
        os.environ['SELENIUM_CACHE_DIR'] = '/tmp/selenium'
        os.environ["HOME"] = "/tmp"
        os.environ["XDG_CACHE_HOME"] = "/tmp"
        os.environ["SELENIUM_CACHE_PATH"] = "/tmp/selenium"
        os.environ["TMPDIR"] = "/tmp"
        self.username = username
        self.password = password

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

        # user_data_dir = tempfile.mkdtemp()
        # chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        try:
            service = Service(
                service_log_path="/tmp/chromedriver.log"
            )
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
        except Exception as e:
            chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

            service = Service(
                executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
                service_log_path="/tmp/chromedriver.log"
            )
        
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )

        self.driver.maximize_window()
        self.driver.get(BETHPAGE_TEE_TIMES_WEBSITE_URL)
        self.wait = WebDriverWait(self.driver, 10)
        self.wait_short = WebDriverWait(self.driver, 0.5)

    def get_tee_time_data(self):
        if not self.login():
            logger.error("Login failed, aborting scrape")
            return []

        if not self.move_to_calendar_page():
            logger.error("Failed to navigate to calendar page, aborting scrape")
            return []

        tee_times = []
        days_checked = []
        next_day_to_check = self.get_available_day(days_checked, True)
        while next_day_to_check:
            next_day_formatted = DateHandler().get_date_from_day_number(next_day_to_check.text)
            days_checked.append(next_day_to_check.text)

            self.driver.execute_script("arguments[0].click();", next_day_to_check)
            self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "td.active.day"))
            )

            self.add_available_times_from_day(next_day_formatted, tee_times)
            next_day_to_check = self.get_available_day(days_checked)

        logger.info("Scraped %d tee times from %d days", len(tee_times), len(days_checked))
        self.driver.quit()
        return tee_times

    def add_available_times_from_day(self, day_formatted, tee_times):
        time.sleep(0.5)
        for i in range(5):
            try:
                time_tiles = self.driver.find_elements(
                    By.CSS_SELECTOR, "div.time.time-tile"
                )
                if not len(time_tiles):
                    if self.driver.find_elements(
                        By.XPATH,
                        "//h1[text()='Use Time/Day filters to find desired teetime']",
                    ):
                        logger.debug("No tee times available on %s", day_formatted)
                        return
                    time.sleep(0.25)
                    continue

                logger.debug("Found %d tee times on %s", len(time_tiles), day_formatted)
                for tile in time_tiles:
                    self.add_time_to_dict(tile, tee_times, day_formatted)
                return

            except Exception as e:
                if self.driver.find_elements(
                    By.XPATH,
                    "//h1[text()='Use Time/Day filters to find desired teetime']",
                ):
                    logger.debug("No tee times available on %s", day_formatted)
                    return
                if i < 4:
                    time.sleep(0.25)
                    logger.debug("Retrying tee time retrieval for %s (attempt %d)", day_formatted, i + 1)
                    continue
                logger.error("Failed to retrieve tee times for %s after %d attempts: %s", day_formatted, i + 1, str(e))

    def add_time_to_dict(self, tile, tee_times, day):
        start_time = tile.find_element(
            By.CSS_SELECTOR, "div.booking-start-time-label"
        ).text

        holes_span = tile.find_element(
            By.CSS_SELECTOR, "span.booking-slot-holes.js-booking-slot-holes"
        )
        holes_number = holes_span.find_element(By.TAG_NAME, "span").text

        players_span = tile.find_element(
            By.CSS_SELECTOR, "span.booking-slot-players.js-booking-slot-players"
        )
        players_number = players_span.find_element(By.TAG_NAME, "span").text

        tee_times.append(
            {"Date": day, "Time": start_time, "Players": players_number, "Holes": holes_number}
        )

    def get_available_day(self, days_checked, log_days=False):
        days = []
        current_day_cell = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "td.active.day"))
        )
        days.append(current_day_cell)

        day_divs = self.driver.find_elements(By.XPATH, "//td[@class='day']")
        days.extend(day_divs)

        next_month_day_divs = self.driver.find_elements(
            By.XPATH, "//td[@class='new day']"
        )
        days.extend(next_month_day_divs)

        unchecked_days = [d for d in days if d.text not in days_checked]

        if log_days:
            all_days_text = [d.text for d in days]
            logger.debug("Available days to check: %s", ', '.join(all_days_text))

        return unchecked_days[0] if unchecked_days else None

    def has_current_date_button(self):
        current_day = self.wait_short.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "td.active.day"))
        ).text
        return current_day != None

    def login(self):
        for i in range(5):
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, "a.login")
                self.driver.execute_script("arguments[0].click();", login_button)

                email_input = self.driver.find_element(By.ID, "login_email")
                password_input = self.driver.find_element(By.ID, "login_password")

                email_input.send_keys(self.username)
                password_input.send_keys(self.password)

                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.login"))
                )
                self.driver.execute_script("arguments[0].click();", login_button)

                logger.info("Successfully logged in to Bethpage website")
                return True
            except Exception as e:
                if i < 4:
                    time.sleep(0.5)
                    self.driver.save_screenshot("login_fail.png")
                    logger.debug("Login attempt %d failed, retrying", i + 1)
                    continue
                logger.error("Login failed after %d attempts: %s", i + 1, str(e))
                return False

    def select_desired_course(self):
        """
        Select the desired course from the facility dropdown.
        Returns True if a desired course is found and selected, False otherwise.
        """
        try:
            # Wait longer for the page to fully load after clicking resident button
            logger.debug("Waiting for course dropdown to appear...")

            # Use a longer wait specifically for the dropdown
            wait_long = WebDriverWait(self.driver, 30)  # 30 second wait

            # Try to find the dropdown with multiple strategies
            dropdown = None
            selectors = [
                (By.ID, "schedule_select", "ID"),
                (By.NAME, "schedules", "name"),
                (By.CLASS_NAME, "schedules", "class"),
            ]

            for by, selector, desc in selectors:
                try:
                    logger.debug("Trying to find dropdown by %s: %s", desc, selector)
                    dropdown = wait_long.until(EC.presence_of_element_located((by, selector)))
                    logger.info("✓ Found dropdown by %s", desc)
                    break
                except Exception as e:
                    logger.debug("✗ Dropdown not found by %s: %s", desc, str(e))
                    continue

            if not dropdown:
                logger.error("Could not find dropdown with any selector")
                self.driver.save_screenshot("/tmp/no_dropdown_found.png")
                return False

            # Save screenshot for debugging
            try:
                self.driver.save_screenshot("/tmp/before_course_select.png")
                logger.debug("Screenshot saved to /tmp/before_course_select.png")
            except:
                pass

            select = Select(dropdown)
            all_options = select.options

            # Log available courses for debugging
            available_courses = [opt.text.strip() for opt in all_options]
            logger.info("Available courses: %s", ', '.join(available_courses))

            # Look for any of the desired courses
            for option in all_options:
                option_text = option.text.strip()
                for desired_course in DESIRED_COURSES:
                    if desired_course in option_text:
                        logger.info("Found desired course: %s", option_text)
                        select.select_by_visible_text(option_text)
                        time.sleep(0.5)  # Wait for page to update after selection
                        return True

            # No desired course found
            logger.warning("Desired course(s) %s not found in available options: %s",
                         DESIRED_COURSES, ', '.join(available_courses))
            return False

        except Exception as e:
            logger.error("Failed to select course from dropdown: %s", str(e))
            # Save screenshot on error
            try:
                self.driver.save_screenshot("/tmp/course_select_error.png")
                logger.error("Error screenshot saved to /tmp/course_select_error.png")
            except:
                pass
            return False

    def move_to_calendar_page(self):
        for i in range(5):
            try:
                logger.debug("Navigating to tee times page")

                resident_button = self.wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[normalize-space(text())='Verified NYS Resident - Bethpage/Sunken Meadow']",
                        )
                    )
                )
                self.driver.execute_script("arguments[0].click();", resident_button)

                # Select the desired course from the dropdown
                if not self.select_desired_course():
                    logger.error("Could not select desired course, aborting")
                    return False

                if self.has_current_date_button():
                    logger.info("Successfully navigated to tee times page")
                    return True

            except Exception as e:
                if i < 4:
                    time.sleep(0.75)
                    logger.debug("Navigation attempt %d failed, retrying", i + 1)
                    continue
                logger.error("Failed to navigate to tee times page after %d attempts: %s", i + 1, str(e))
                return False
