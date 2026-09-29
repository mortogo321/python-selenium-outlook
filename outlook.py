"""Selenium browser-automation demo: log in to Outlook webmail and list inbox subjects.

Demonstrates stealth Chrome configuration, resilient explicit waits, and DOM
scraping of a dynamic web UI. Credentials are read from the environment when
set (``OUTLOOK_EMAIL`` / ``OUTLOOK_PASSWORD``) and otherwise prompted for
interactively — they are never written to disk or logged.

Requires Chrome + a matching chromedriver. Selenium >= 4.6 ships Selenium
Manager, which downloads the correct driver automatically, so no manual
chromedriver install is needed.
"""

from __future__ import annotations

import getpass
import logging
import os
import random
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

LOGIN_URL = os.getenv("OUTLOOK_LOGIN_URL", "https://outlook.live.com/owa/")
DEFAULT_TIMEOUT = int(os.getenv("OUTLOOK_TIMEOUT", "20"))
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def get_credentials() -> tuple[str, str]:
    """Return (email, password) from env or interactive prompts."""
    email = os.getenv("OUTLOOK_EMAIL") or input("Enter your Outlook email: ")
    password = os.getenv("OUTLOOK_PASSWORD") or getpass.getpass("Enter your password: ")
    if not email or not password:
        raise ValueError("Email and password must not be empty.")
    return email, password


def get_chrome_options(headless: bool = True) -> ChromeOptions:
    """Build hardened Chrome options for automation.

    Deliberately omits the insecure flags from the original demo
    (``--disable-web-security`` / ``--allow-running-insecure-content``).
    """
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")  # required when running as root in Docker
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")

    if headless:
        options.add_argument("--headless=new")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    user_agent = os.getenv("OUTLOOK_USER_AGENT", DEFAULT_USER_AGENT)
    options.add_argument(f"user-agent={user_agent}")
    return options


def create_driver(headless: bool = True) -> WebDriver:
    """Create a Chrome driver with stealth tweaks (driver via Selenium Manager)."""
    driver = webdriver.Chrome(options=get_chrome_options(headless=headless))
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """,
        },
    )
    return driver


def human_delay(min_seconds: float = 0.5, max_seconds: float = 2.5) -> None:
    """Sleep a random short interval to mimic human pacing (not cryptographic)."""
    time.sleep(random.uniform(min_seconds, max_seconds))  # noqa: S311


def login(
    driver: WebDriver, email: str, password: str, timeout: int = DEFAULT_TIMEOUT
) -> None:
    """Submit the Microsoft login form."""
    logger.info("Logging in..")
    human_delay()
    driver.get(LOGIN_URL)

    email_field = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.NAME, "loginfmt"))
    )
    email_field.send_keys(email)

    next_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    next_button.click()

    password_field = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.NAME, "passwd"))
    )
    password_field.send_keys(password)

    sign_in_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    sign_in_button.click()


def dismiss_stay_signed_in(driver: WebDriver, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Click through the optional 'Stay signed in?' prompt. Returns True if handled."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Stay signed in?')]")
            )
        )
        yes_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
        )
        yes_button.click()
        logger.info("Clicked 'Yes' on 'Stay signed in?' prompt.")
        return True
    except TimeoutException:
        logger.info("No 'Stay signed in?' prompt found.")
        return False


def open_inbox(driver: WebDriver, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Click the Inbox link. Returns True on success."""
    try:
        inbox_link = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Inbox' or contains(text(), 'Inbox')]")
            )
        )
        inbox_link.click()
        logger.info("Successfully clicked Inbox link.")
        return True
    except TimeoutException:
        logger.warning("Failed to click Inbox link within timeout period.")
        return False


def list_inbox_subjects(driver: WebDriver, timeout: int = DEFAULT_TIMEOUT) -> list[str]:
    """Return the subject lines of currently visible inbox messages."""
    try:
        mail_list_div: WebElement = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "MailList"))
        )
        email_titles = mail_list_div.find_elements(By.CSS_SELECTOR, "span.TtcXM")
        subjects = [title.text for title in email_titles]
        for subject in subjects:
            logger.info("--> %s", subject)
        return subjects
    except TimeoutException:
        logger.warning("MailList div not found within the timeout period.")
        return []


def run(
    email: str,
    password: str,
    *,
    headless: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[str]:
    """Run the full login → inbox → subjects flow and return subjects."""
    driver = create_driver(headless=headless)
    try:
        login(driver, email, password, timeout=timeout)
        dismiss_stay_signed_in(driver, timeout=timeout)
        open_inbox(driver, timeout=timeout)
        logger.info("Listing inbox emails:")
        return list_inbox_subjects(driver, timeout=timeout)
    finally:
        driver.quit()


def _headless_from_env() -> bool:
    return os.getenv("OUTLOOK_HEADLESS", "1").lower() not in {"0", "false", "no"}


def main() -> int:
    """CLI entrypoint. Returns process exit code."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        email, password = get_credentials()
    except ValueError as exc:
        logger.error("%s", exc)
        return 2
    try:
        run(email, password, headless=_headless_from_env(), timeout=DEFAULT_TIMEOUT)
    except Exception as exc:  # noqa: BLE001 - demo script reports and exits non-zero
        logger.error("An error occurred: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
