# whatsapp.py
import time
import urllib.parse
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ------------------ Logging ------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ------------------ Global Driver ------------------
_driver = None


def get_driver(persist_profile_dir="./chrome_data", headless=False):
    """
    Initialize a Chrome WebDriver with persistent user data.
    Keeps WhatsApp logged in across sessions.
    """
    global _driver
    if _driver:
        return _driver

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={persist_profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    if headless:
        chrome_options.add_argument("--headless=new")

    # ✅ Correct setup for new Selenium
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)

    _driver = driver
    return driver


def send_whatsapp_message(phone_e164: str, message: str, wait_for_sent: bool = True, timeout: int = 30):
    """
    Send a WhatsApp message using WhatsApp Web automation.
    :param phone_e164: Phone number in E.164 format (e.g. '+919876543210')
    :param message: Text message to send
    """
    driver = get_driver()

    # Construct WhatsApp Web URL
    text_enc = urllib.parse.quote(message)
    phone_digits = phone_e164.replace("+", "")
    url = f"https://web.whatsapp.com/send?phone={phone_digits}&text={text_enc}"

    try:
        driver.get(url)
    except Exception as e:
        logger.warning("Initial page load issue: %s", e)
        driver.get("https://web.whatsapp.com")
        time.sleep(5)
        driver.get(url)

    wait = WebDriverWait(driver, timeout)

    # Wait for the message box or chat window to load
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@contenteditable='true' and @data-tab='10']")
            )
        )
        time.sleep(2)
    except Exception:
        raise RuntimeError("⚠️ WhatsApp Web not logged in. Please scan QR in the opened browser.")

    # Try to click send button
    try:
        send_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='compose-btn-send']"))
        )
        send_btn.click()
        logger.info("✅ Message sent successfully.")
    except Exception:
        # Fallback: press Enter key to send
        try:
            input_box = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @data-tab='10']")
            input_box.send_keys("\n")
            logger.info("✅ Message sent using ENTER key.")
        except Exception as e:
            logger.error("❌ Could not send message: %s", e)
            raise

    if wait_for_sent:
        time.sleep(2)
    return {"status": "sent", "phone": phone_e164}


# ------------------ Direct Test Run ------------------
if __name__ == "__main__":
    # 👇 Example: Run directly to test it
    phone = "+917204619128"  # change this to your number
    msg = "Hello! This is a test message from Selenium WhatsApp automation."
    print(send_whatsapp_message(phone, msg))
