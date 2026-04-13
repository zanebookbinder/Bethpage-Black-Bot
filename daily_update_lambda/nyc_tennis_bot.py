import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

NYC_TENNIS_URL = "https://www.nycgovparks.org/tennisreservation"
NOT_LIVE_MARKER = "Online court reservations will open over the coming weeks"


class NycTennisBot:
    def scrape_data_and_return_email_html(self):
        logger.info("Checking NYC tennis reservation page")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(NYC_TENNIS_URL, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            if NOT_LIVE_MARKER in soup.get_text():
                logger.info("Tennis reservations not yet live")
                return ""
            logger.info("Tennis reservations appear to be live!")
            return '<h2 style="color: red;">NYC TENNIS RESERVATIONS ARE LIVE NOW</h2>'
        except Exception as e:
            logger.error("Error checking tennis reservations: %s", str(e))
            return ""
