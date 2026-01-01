import json
from typing import List
from .travel_time_calculation_service import TravelTimeCalculationService
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class NewYorkCaresWebScraper:
    """Simplified scraper for New York Cares project cards.

    Expects cards with class containing `project-card-default` and a child
    `<div class="hidden">` containing a JSON object (see provided sample).

    Returns a list of dicts with keys: `title`, `date`, `time`, `location`, `link`, `description`.
    """

    BASE_URL = "https://www.newyorkcares.org/volunteers?boroughs%5B%5D=Manhattan&days%5B%5D=Saturday&days%5B%5D=Sunday"

    def __init__(self, url: str = None):
        self.url = url or self.BASE_URL

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
            "Chrome/143.0.7499.170 Safari/537.36"
        )

        try:
            # service = Service(service_log_path="/tmp/chromedriver.log")
            self.driver = webdriver.Chrome(options=chrome_options)
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

        self.travel_time_service = TravelTimeCalculationService()

    def find_weekend_opportunities(self) -> List[dict]:
        """Render the page with Selenium and extract opportunity JSON from hidden divs.

        This approach ensures client-side rendered cards are available.
        """
        print("Scraping New York Cares for weekend volunteering opportunities...")

        results = []
        try:
            self.driver.get(self.url)
            # wait for at least one project card to appear
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[class*="project-card-default"]')
                )
            )

            # find all project-card-default containers
            cards = self.driver.find_elements(
                By.CSS_SELECTOR, 'div[class*="project-card-default"]'
            )

            for card in cards:
                try:
                    hidden = None
                    try:
                        hidden = card.find_element(By.CSS_SELECTOR, "div.hidden")
                    except Exception:
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
                        title = data.get("Web_Title_FF__c") or data.get("Name")
                        date = data.get("StartDate")
                        start_time = data.get("Activity_Start_Time__c")
                        end_time = data.get("Activity_End_Time__c")
                        if start_time and end_time:
                            time_str = f"{self.format_time(start_time)} - {self.format_time(end_time)}"
                        else:
                            time_str = start_time or end_time
                        location = (
                            data.get("Website_Address__c")
                            or data.get("SiteAddress__tl")
                            or (data.get("Site__r") or {}).get("Name")
                        )
                        description = data.get("Project_Description__c")
                    else:
                        # fallback to visible elements
                        try:
                            h2 = card.find_element(By.TAG_NAME, "h2")
                            title = h2.text.strip()
                        except Exception:
                            title = None
                        date = None
                        time_str = None
                        location = None
                        description = None

                    is_full = False
                    if data:
                        # JSON flags from the sample
                        if data.get("Full_Capacity_Boolean__c") is True:
                            is_full = True
                        elif str(data.get("Full_Capacity__c", "")).strip().lower() in (
                            "yes",
                            "true",
                            "y",
                        ):
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
                        except Exception:
                            pass

                    if is_full:
                        continue

                    # find link
                    link = None
                    try:
                        link_el = card.find_element(
                            By.CSS_SELECTOR, 'a[href^="/project/"]'
                        )
                        href = link_el.get_attribute("href")
                        link = href
                    except Exception:
                        link = None

                    if not title or not date or not time_str or not location:
                        continue

                    if location:
                        transit_time = self.travel_time_service.get_travel_time(
                            location, "transit"
                        )
                        walking_time = self.travel_time_service.get_travel_time(
                            location, "walking"
                        )
                    else:
                        transit_time = None
                        walking_time = None

                    results.append(
                        {
                            "title": title,
                            "date": date,
                            "time": time_str,
                            "location": location,
                            "link": link,
                            "description": description,
                            "transit_time": transit_time,
                            "walking_time": walking_time,
                        }
                    )
                except Exception as e:
                    print(f"Skipping card due to error: {e}")
                    continue

        except Exception as e:
            print(f"Error rendering page or finding cards: {e}")
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

        print("Found", len(results), "New York Cares opportunities.")
        return results

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
