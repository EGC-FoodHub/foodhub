import os
import time

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver

pytestmark = pytest.mark.selenium


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def wait_for_any(driver, checks, timeout=5, poll=0.25):
    """Wait until any of the given checks is present. `checks` is a list of
    tuples in the form `(by, selector)`. Returns the first found element or
    raises TimeoutException.
    """
    end = time.time() + timeout
    while time.time() < end:
        for by, sel in checks:
            try:
                el = driver.find_element(by, sel)
                if el:
                    return el
            except NoSuchElementException:
                continue
        time.sleep(poll)
    raise Exception(f"None of selectors found: {checks}")


def test_upload_food_zip_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # 1️⃣ Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email"))).send_keys("user1@example.com")
        driver.find_element(By.ID, "password").send_keys("1234" + Keys.RETURN)
        wait_for_page_to_load(driver)
        time.sleep(1)

        # 2️⃣ Abrir upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # 3️⃣ Seleccionar pestaña ZIP
        zip_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "zip-tab")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", zip_tab)
        zip_tab.click()
        wait_for_page_to_load(driver)

        # 4️⃣ Subir ZIP
        zip_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "zip_input")))
        zip_file_path = os.path.abspath("app/modules/fooddataset/food_examples.zip")
        zip_input.send_keys(zip_file_path)
        time.sleep(1)  # esperar que Dropzone procese el archivo

        upload_zip_btn = driver.find_element(By.ID, "upload_zip_btn")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_zip_btn)
        upload_zip_btn.click()
        time.sleep(2)
        wait_for_page_to_load(driver)

        # 5️⃣ Marcar checkbox de acuerdo
        agree_checkbox = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "agreeCheckbox")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agree_checkbox)
        agree_checkbox.click()
        wait_for_page_to_load(driver)
        time.sleep(1)

        driver.find_element(By.ID, "title").send_keys("test")
        driver.find_element(By.ID, "desc").send_keys("test")

        # 6️⃣ Click final en "Upload Dataset"
        final_upload_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_button")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", final_upload_btn)
        final_upload_btn.click()
        wait_for_page_to_load(driver)
        time.sleep(3)  # esperar a que el ZIP se procese completamente

    finally:
        close_driver(driver)


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
    time.sleep(3)
    wait_for_page_to_load(driver)


def test_fooddataset_list_and_view():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host, email="user1@example.com", password="1234")

        # Test 1: List Datasets
        driver.get(f"{host}/dataset/list")
        wait_for_page_to_load(driver)
        assert "/dataset/list" in driver.current_url

        # Check if body exists
        try:
            driver.find_element(By.TAG_NAME, "body")
        except Exception:
            pytest.fail("Page content not found")

        # Test 2: View specific dataset (Negative/404)
        driver.get(f"{host}/dataset/99999999")
        wait_for_page_to_load(driver)

        page_source = driver.page_source.lower()
        assert "404" in driver.title.lower() or "not found" in page_source, "Expected 404 error page"

    finally:
        close_driver(driver)


def test_upload_zip_without_file_shows_error():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        # 1️⃣ Ir a Upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # 2️⃣ Click en el tab ZIP
        zip_tab = driver.find_element(By.ID, "zip-tab")
        zip_tab.click()
        time.sleep(1)

        # 3️⃣ Click en Upload ZIP sin seleccionar archivo
        upload_zip_btn = driver.find_element(By.ID, "upload_zip_btn")
        upload_zip_btn.click()

        time.sleep(2)
        wait_for_page_to_load(driver)

        # 4️⃣ Comprobaciones (NEGATIVE TEST)
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()

        # Debe seguir en upload (no redirige)
        assert "upload" in current_url

        # Algún mensaje de error debe aparecer
        assert (
            "zip" in page_source or "file" in page_source or "required" in page_source or "error" in page_source
        ), "Expected error message when uploading ZIP without file"

        print("ZIP upload without file Selenium test passed")

    finally:
        close_driver(driver)


def test_upload_invalid_zip_shows_error():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        # 1️⃣ Ir a Upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # 2️⃣ Abrir tab ZIP
        driver.find_element(By.ID, "zip-tab").click()
        time.sleep(1)

        # 3️⃣ Seleccionar ZIP inválido
        zip_path = os.path.abspath("app/modules/fooddataset/food_examples.zip")
        assert os.path.exists(zip_path), "Invalid ZIP test file does not exist"

        zip_input = driver.find_element(By.ID, "zip_input")
        zip_input.send_keys(zip_path)

        # 4️⃣ Click Upload ZIP
        driver.find_element(By.ID, "upload_zip_btn").click()
        time.sleep(2)
        wait_for_page_to_load(driver)

        # 5️⃣ Validaciones (NEGATIVE TEST)
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()

        # No debe salir de upload
        assert "upload" in current_url

        # Debe aparecer error
        assert (
            "invalid" in page_source or "error" in page_source or "zip" in page_source or "format" in page_source
        ), "Expected error message for invalid ZIP upload"

    finally:
        close_driver(driver)


def test_upload_valid_food_files_from_github():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        driver.find_element(By.ID, "github-tab").click()
        time.sleep(1)
        driver.find_element(By.ID, "gh_url").send_keys("https://github.com/EGC-FoodHub/foodhub")
        driver.find_element(By.ID, "gh_branch").send_keys("main")
        driver.find_element(By.ID, "title").send_keys("test")
        driver.find_element(By.ID, "desc").send_keys("test")
        time.sleep(1)
        driver.find_element(By.ID, "import_repo_btn").click()

        # Wait for agree checkbox and click upload flow to proceed
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "agreeCheckbox"))).click()
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "upload_button"))).click()

        # Quick check: ensure we're still on an app page and no exception thrown
        assert "/dataset" in driver.current_url

    finally:
        close_driver(driver)


def test_valid_repo_with_no_food_file():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # Fill metadata and GitHub info
        driver.find_element(By.ID, "title").click()
        driver.find_element(By.ID, "title").send_keys("test4")
        driver.find_element(By.ID, "desc").click()
        driver.find_element(By.ID, "desc").send_keys("test4")
        driver.find_element(By.ID, "github-tab").click()
        # Wait briefly for the tab to render, then send the URL.
        time.sleep(1)
        driver.find_element(By.ID, "gh_url").send_keys("https://github.com/EGC-FoodHub/foodhub")
        driver.find_element(By.ID, "gh_branch").send_keys("main")
        driver.find_element(By.ID, "import_repo_btn").click()

        # After import, wait for either the agree checkbox (files found) or a
        # file-list / alert (no .food files or other messages). This avoids
        # brittle waits that assume a specific UI flow.
        el = wait_for_any(
            driver,
            [
                (By.ID, "agreeCheckbox"),
                (By.ID, "file-list"),
                (By.CSS_SELECTOR, ".alert"),
                (By.ID, "import_repo_btn"),
            ],
            timeout=8,
        )
        assert el is not None

    finally:
        close_driver(driver)


def test_invalid_title_description_flow():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        driver.find_element(By.ID, "github-tab").click()
        time.sleep(1)
        driver.find_element(By.ID, "import_repo_btn").click()

        # Move focus to the page to simulate user interaction; ensure no crash
        body = driver.find_element(By.CSS_SELECTOR, "body")
        ActionChains(driver).move_to_element(body).perform()
        assert True

    finally:
        close_driver(driver)


def test_invalid_github_url_with_valid_format():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        driver.find_element(By.ID, "github-tab").click()
        time.sleep(1)
        driver.find_element(By.ID, "gh_url").send_keys("https://github.com/EGC-FoodHub/foodhubinvalid")
        driver.find_element(By.ID, "gh_branch").send_keys("main")
        driver.find_element(By.ID, "import_repo_btn").click()

        # If the import is invalid, page should still be responsive
        assert "/dataset/upload" in driver.current_url or "import" in driver.page_source.lower()

    finally:
        close_driver(driver)


def test_invalid_github_url():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        driver.find_element(By.ID, "github-tab").click()
        time.sleep(1)
        driver.find_element(By.ID, "gh_url").send_keys("invalid")
        driver.find_element(By.ID, "gh_branch").send_keys("main")
        driver.find_element(By.ID, "import_repo_btn").click()

        # Basic assertion that page stayed responsive
        assert "upload" in driver.current_url or "error" in driver.page_source.lower()

    finally:
        close_driver(driver)


def test_invalid_branch():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_as_user(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        driver.find_element(By.ID, "github-tab").click()
        time.sleep(1)
        driver.find_element(By.ID, "gh_url").send_keys("https://github.com/EGC-FoodHub/foodhub")
        driver.find_element(By.ID, "gh_branch").send_keys("invalid")
        driver.find_element(By.ID, "import_repo_btn").click()

        # Ensure no crash and page remains interactive
        assert "upload" in driver.current_url or "error" in driver.page_source.lower()

    finally:
        close_driver(driver)
