import json
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from daily_update_helpers.chrome_helper import create_headless_chrome_driver
from daily_update_helpers.daily_update_constants import NEW_YORK_CARES_BASE_URL
from daily_update_helpers.travel_time_calculation_service import (
    TravelTimeCalculationService,
)


class NewYorkCaresWebScraper:
    """Scraper for New York Cares project cards. Expects cards with `project-card-default`
    and a child `<div class="hidden">` containing JSON. Returns dicts with
    `title`, `date`, `time`, `location`, `link`, `description`."""

    def __init__(self, url: str = None):
        self.url = url or NEW_YORK_CARES_BASE_URL
        self.driver, self.wait = create_headless_chrome_driver(wait_seconds=10)
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
                        title = data.get("Public_Session_Name__c") or data.get("Name")
                        date = data.get("Session_Start_Date__c")
                        start_time = data.get("Session_Start_Time_Formatted__c")
                        end_time = data.get("Session_End_Time_Formatted__c")
                        if start_time and end_time:
                            time_str = f"{start_time} - {end_time}"
                        else:
                            time_str = start_time or end_time
                        location = (
                            data.get("Address__c")
                            or data.get("Location_Address__tl")
                        )
                        description = data.get("Description__c")
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
