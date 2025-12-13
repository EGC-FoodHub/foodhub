import time

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


@pytest.mark.selenium
def test_login_and_check_element():
    """Selenium E2E: open login page, submit, and check for dashboard heading."""

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)

        # Wait a little while to ensure that the action has been completed
        time.sleep(4)

        try:
            driver.find_element(By.XPATH, "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]")
        except NoSuchElementException:
            pytest.fail("Expected dashboard heading not found after login")

    finally:
        # Close the browser
        close_driver(driver)
<<<<<<< HEAD
=======


def test_inserting_invalid_2fa_when_login():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(host)
        login_page_link = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.LINK_TEXT, "Login")))
        login_page_link.click()
        driver.find_element(By.ID, "email").click()
        driver.find_element(By.ID, "email").send_keys("user3@example.com")
        driver.find_element(By.ID, "password").click()
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        driver.find_element(By.ID, "code").click()
        driver.find_element(By.ID, "code").send_keys("111111")
        driver.find_element(By.ID, "submit").click()
    finally:
        close_driver(driver)


def test_fail_activate_2fa():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(host)
        login_page_link = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.LINK_TEXT, "Login")))
        login_page_link.click()
        driver.find_element(By.ID, "email").click()
        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "password").click()
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        edit_prof_link = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.LINK_TEXT, "Edit profile")))
        edit_prof_link.click()
        activate_2fa_link = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.LINK_TEXT, "Activar 2FA")))
        activate_2fa_link.click()
        driver.find_element(By.ID, "code").click()
        driver.find_element(By.ID, "code").send_keys("444444")
        driver.find_element(By.ID, "submit").click()
    finally:
        close_driver(driver)


# Call the test function
test_login_and_check_element()
test_inserting_invalid_2fa_when_login()
test_fail_activate_2fa()
>>>>>>> fix-g2/57-fakenodo-connection
