import os
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


@pytest.mark.selenium
def test_dataset_upload_check():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/login")
        time.sleep(2)
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)
        time.sleep(2)

        driver.get(f"{host}/dataset/upload")
        time.sleep(2)

        temp_file_path = os.path.join(os.getcwd(), "selenium_test.food")
        with open(temp_file_path, "w") as f:
            f.write("name: SeleniumTest\ncalories: 100\ntype: TestFood")

        try:
            time.sleep(1)

            # Make hidden input visible
            driver.execute_script("document.querySelector('.dz-hidden-input').style.visibility = 'visible';")
            driver.execute_script("document.querySelector('.dz-hidden-input').style.height = '1px';")
            driver.execute_script("document.querySelector('.dz-hidden-input').style.width = '1px';")
            driver.execute_script("document.querySelector('.dz-hidden-input').style.opacity = 1;")

            dropzone_input = driver.find_element(By.CSS_SELECTOR, ".dz-hidden-input")
            dropzone_input.send_keys(temp_file_path)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.badge.bg-success"))
            )

            success_badge = driver.find_element(By.CSS_SELECTOR, "span.badge.bg-success")
            badge_text = success_badge.text.strip()

            print(f"Badge text detected: '{badge_text}'")
            assert "Valid: TestFood" in badge_text
        
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        print(f"Test failed with error: {e}")
        raise e

    finally:
        close_driver(driver)
