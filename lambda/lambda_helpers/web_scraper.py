from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lambda_helpers.date_handler import DateHandler
import time
import os

BETHPAGE_TEE_TIMES_WEBSITE_URL = 'https://foreupsoftware.com/index.php/booking/19765/2431#/teetimes'

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
            print("Couldn't log in. Exiting...")
            return []

        if not self.move_to_calendar_page():
            print("Couldn't move to calendar page. Exiting...")
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

        print(f"Found {len(tee_times)} tee times")
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
                        print(f"No times on {day_formatted}")
                        return
                    time.sleep(0.25)
                    continue

                print(f'Found {len(time_tiles)} times on {day_formatted}')
                for tile in time_tiles:
                    self.add_time_to_dict(tile, tee_times, day_formatted)
                return

            except Exception as e:
                if self.driver.find_elements(
                    By.XPATH,
                    "//h1[text()='Use Time/Day filters to find desired teetime']",
                ):
                    print(f"No times on {day_formatted}")
                    return
                if i < 4:
                    time.sleep(0.25)
                    print(f"Retrying for the {i} time")
                    continue
                print(
                    f"Error during tee time retrieval after {i} tries with {day_formatted}:\n",
                    e,
                )

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

    def get_available_day(self, days_checked, print_results=False):
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
        all_days_text = [d.text for d in days]

        if print_results:
            print('All days:', ', '.join(all_days_text))

        return unchecked_days[0] if unchecked_days else None

    def has_current_date_button(self):
        current_day = self.wait_short.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "td.active.day"))
        ).text
        return current_day != None

    def login(self):
        for i in range(5):
            try:
                # Find and click the login button
                login_button = self.driver.find_element(By.CSS_SELECTOR, "a.login")
                self.driver.execute_script("arguments[0].click();", login_button)

                # Find username/email and password input fields by their IDs
                email_input = self.driver.find_element(By.ID, "login_email")
                password_input = self.driver.find_element(By.ID, "login_password")

                # Enter your credentials
                email_input.send_keys(self.username)
                password_input.send_keys(self.password)

                # Submit form by pressing Enter in the password field
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.login"))
                )
                self.driver.execute_script("arguments[0].click();", login_button)

                print("Logged in successfully!")
                return True
            except Exception as e:
                if i < 4:
                    time.sleep(0.5)
                    self.driver.save_screenshot("login_fail.png")
                    print(f"Retrying for the {i} time")
                    continue
                print(f"Error during login after {i} tries:\n", e)
                return False

    def move_to_calendar_page(self):
        for i in range(5):
            try:
                print("Attempting navigation to tee times page")

                resident_button = self.wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[normalize-space(text())='Verified NYS Resident - Bethpage/Sunken Meadow']",
                        )
                    )
                )
                self.driver.execute_script("arguments[0].click();", resident_button)
                if self.has_current_date_button():
                    print("On tee times page")
                    return True

            except Exception as e:
                if i < 4:
                    time.sleep(0.75)
                    print(f"Retrying for the {i} time")
                    continue
                print(f"Error during login after {i} tries:\n", e)
                return False
