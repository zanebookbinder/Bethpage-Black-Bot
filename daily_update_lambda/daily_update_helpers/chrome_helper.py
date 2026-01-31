"""Shared headless Chrome setup for Selenium web scrapers."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


def create_headless_chrome_driver(wait_seconds: int = 10):
    """
    Create a headless Chrome WebDriver for Lambda/local use.
    Returns (driver, wait) tuple.
    """
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-tools")
    opts.add_argument("--no-zygote")
    opts.add_argument("--single-process")
    opts.add_argument("--remote-debugging-pipe")
    opts.add_argument("--log-path=/tmp")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )

    try:
        service = Service(service_log_path="/tmp/chromedriver.log")
        driver = webdriver.Chrome(service=service, options=opts)
    except Exception:
        opts.binary_location = "/opt/chrome/chrome-linux64/chrome"
        service = Service(
            executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
            service_log_path="/tmp/chromedriver.log",
        )
        driver = webdriver.Chrome(service=service, options=opts)

    driver.maximize_window()
    wait = WebDriverWait(driver, wait_seconds)
    return driver, wait
