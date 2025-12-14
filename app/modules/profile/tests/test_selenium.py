import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver

pytestmark = pytest.mark.selenium


def wait_for_page_to_load(driver, timeout=5):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def test_metrics_after_upload():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # 1. Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "password").send_keys("1234", Keys.RETURN)
        time.sleep(1)

        # 2. Go to upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # 3. Fill minimal form
        driver.find_element(By.NAME, "title").send_keys("Metrics test")
        driver.find_element(By.NAME, "desc").send_keys("Metrics test")

        # 4. File upload
        file_path = os.path.abspath("app/modules/fooddataset/food_examples/pechuga_pollo.food")

        driver.find_element(By.CLASS_NAME, "dz-hidden-input").send_keys(file_path)
        time.sleep(1)

        # 5. Accept and submit
        driver.find_element(By.ID, "agreeCheckbox").send_keys(Keys.SPACE)
        driver.find_element(By.ID, "upload_button").send_keys(Keys.RETURN)
        time.sleep(1)

        # 6. Open first dataset
        driver.find_element(
            By.CSS_SELECTOR, "tr:nth-child(1) .btn-outline-primary"
        ).click()
        wait_for_page_to_load(driver)

        # 7. Go to metrics
        driver.find_element(By.LINK_TEXT, "My metrics").click()
        wait_for_page_to_load(driver)

        # 8. Assertions
        assert "metrics" in driver.current_url.lower()
        assert "No metrics" not in driver.page_source

        print("✅ Metrics test passed")

    finally:
        close_driver(driver)
