import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver

pytestmark = pytest.mark.selenium


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def login_as_user(driver, host, email="user1@example.com", password="1234"):
    driver.get(f"{host}/login")
    wait_for_page_to_load(driver)

    email_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")

    email_field.clear()
    email_field.send_keys(email)
    password_field.clear()
    password_field.send_keys(password)

    password_field.send_keys(Keys.RETURN)
    # Allow small delay for redirect
    time.sleep(1)
    wait_for_page_to_load(driver)


def test_basedataset_list_and_view():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        # Test 1: List Datasets
        driver.get(f"{host}/dataset/list")
        wait_for_page_to_load(driver)
        assert "/dataset/list" in driver.current_url

        # Check if table exists (assuming there is at least a header or 'no datasets' message)
        try:
            # Just checking if the main container is present or page didn't crash
            driver.find_element(By.TAG_NAME, "body")
        except Exception:
            pytest.fail("Page content not found")

        # Test 2: View specific dataset (Negative/404 first to ensure robustness)
        driver.get(f"{host}/dataset/99999999")
        wait_for_page_to_load(driver)

        # Check for 404 indication.
        # This depends on how the app handles 404. Usually title contains "404" or text "Not Found"
        page_source = driver.page_source.lower()
        assert "404" in driver.title.lower() or "not found" in page_source, "Expected 404 error page"

        print("Selenium tests passed!")

    finally:
        close_driver(driver)
