import getpass
import random
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

email = input("Enter your Hotmail email: ")
password = getpass.getpass("Enter your password: ")


def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--headless")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")

    options.add_argument("--disable-extensions")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-component-extensions-with-background-pages")

    if options.arguments.count("--headless"):
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-popup-blocking")

    return options


driver = webdriver.Chrome(options=get_chrome_options())
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    """
    },
)


def human_delay():
    time.sleep(random.uniform(0.5, 2.5))


try:
    human_delay()
    driver.get(
        # login url
        ""
    )

    print("Logging in..")
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "loginfmt"))
    )
    email_field.send_keys(email)

    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    next_button.click()

    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "passwd"))
    )
    password_field.send_keys(password)

    sign_in_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    sign_in_button.click()

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Stay signed in?')]")
            )
        )
        yes_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
        )
        yes_button.click()
        print("Clicked 'Yes' on 'Stay signed in?' prompt.")
    except TimeoutException:
        print("No 'Stay signed in?' prompt found.")

    try:
        inbox_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Inbox' or contains(text(), 'Inbox')]")
            )
        )
        inbox_link.click()
        print("Successfully clicked Inbox link.")
    except TimeoutException:
        print("Failed to click Inbox link within timeout period.")

    print("Listing inbox emails:")

    try:
        mail_list_div = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "MailList"))
        )

        email_titles = mail_list_div.find_elements(By.CSS_SELECTOR, "span.TtcXM")

        for title in email_titles:
            print(f"--> {title.text}")
    except TimeoutException:
        print("MailList div not found within the timeout period.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()
