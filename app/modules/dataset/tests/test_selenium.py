import os
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets

"""
@pytest.mark.selenium
def test_upload_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        time.sleep(4)
        wait_for_page_to_load(driver)

        # Count initial datasets
        initial_datasets = count_datasets(driver, host)

        # Open the upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # Find basic info and UVL model and fill values
        title_field = driver.find_element(By.NAME, "title")
        title_field.send_keys("Title")
        desc_field = driver.find_element(By.NAME, "desc")
        desc_field.send_keys("Description")
        tags_field = driver.find_element(By.NAME, "tags")
        tags_field.send_keys("tag1,tag2")

        # Add two authors and fill
        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field0 = driver.find_element(By.NAME, "authors-0-name")
        name_field0.send_keys("Author0")
        affiliation_field0 = driver.find_element(By.NAME, "authors-0-affiliation")
        affiliation_field0.send_keys("Club0")
        orcid_field0 = driver.find_element(By.NAME, "authors-0-orcid")
        orcid_field0.send_keys("0000-0000-0000-0000")

        name_field1 = driver.find_element(By.NAME, "authors-1-name")
        name_field1.send_keys("Author1")
        affiliation_field1 = driver.find_element(By.NAME, "authors-1-affiliation")
        affiliation_field1.send_keys("Club1")

        # Obtén las rutas absolutas de los archivos
        file1_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
        file2_path = os.path.abspath("app/modules/dataset/uvl_examples/file2.uvl")

        # Subir el primer archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        time.sleep(2)

        # Subir el segundo archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        time.sleep(2)

        # Add authors in UVL models - Wait for button to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "0_button"))
        )
        show_button = driver.find_element(By.ID, "0_button")
        show_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "0_form_authors_button"))
        )
        add_author_uvl_button = driver.find_element(By.ID, "0_form_authors_button")
        add_author_uvl_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field = driver.find_element(By.NAME, "feature_models-0-authors-2-name")
        name_field.send_keys("Author3")
        affiliation_field = driver.find_element(By.NAME, "feature_models-0-authors-2-affiliation")
        affiliation_field.send_keys("Club3")

        # Check I agree and send form
        check = driver.find_element(By.ID, "agreeCheckbox")
        check.send_keys(Keys.SPACE)
        wait_for_page_to_load(driver)

        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        time.sleep(2)  # Force wait time

        assert driver.current_url == f"{host}/dataset/list", "Test failed!"

        # Count final datasets
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 1, "Test failed!"

        print("Test passed!")

    finally:
        # Close the browser
        close_driver(driver)

        
"""


@pytest.mark.selenium
def test_upload_github_repo():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Abrir login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Completar login
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        password_field = driver.find_element(By.ID, "password")
        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        driver.find_element(By.ID, "submit").click()
        wait_for_page_to_load(driver)
        time.sleep(1)

        # Ir a la sección de datasets
        sidebar_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".sidebar-item:nth-child(6) .align-middle:nth-child(2)"))
        )
        sidebar_item.click()
        wait_for_page_to_load(driver)

        # Cambiar a la pestaña GitHub
        github_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "github-tab"))
        )
        github_tab.click()

        # Introducir URL del repositorio
        gh_url_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gh_url"))
        )
        gh_url_input.send_keys("https://github.com/EGC-FoodHub/foodhub")

        # Click en botón importar repositorio
        import_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "import_repo_btn"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", import_btn)
        import_btn.click()
        wait_for_page_to_load(driver)
        time.sleep(1)

        # Aceptar términos
        agree_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "agreeCheckbox"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agree_checkbox)
        agree_checkbox.click()

        # Click en botón final de subir
        upload_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "upload_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_btn)
        upload_btn.click()
        wait_for_page_to_load(driver)
        time.sleep(1)

        # Completar título y descripción
        driver.find_element(By.ID, "title").send_keys("test")
        driver.find_element(By.ID, "desc").send_keys("test")

        # Click final en subir
        # Botón final subir dataset
        upload_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "upload_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_btn)
        upload_btn.click()

        print("Subida de repositorio GitHub completada correctamente!")

    finally:
        close_driver(driver)


@pytest.mark.selenium
def test_invalidbranch():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/")
        driver.set_window_size(810, 1063)

        # Click Login
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Login"))
        ).click()

        # Optional extra click present in the recorded test (may not exist in all layouts)
        try:
            driver.find_element(By.CSS_SELECTOR, ".row:nth-child(2) > .col-md-6 > .mb-3").click()
        except Exception:
            pass

        # Fill credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email"))).click()
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "submit").click()

        # Open sidebar / datasets
        try:
            driver.find_element(By.CSS_SELECTOR, ".hamburger").click()
        except Exception:
            try:
                driver.find_element(By.CSS_SELECTOR, ".sidebar-toggle").click()
            except Exception:
                pass

        sidebar_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".sidebar-item:nth-child(6) .align-middle:nth-child(2)"))
        )
        sidebar_item.click()
        wait_for_page_to_load(driver)

        # Fill basic dataset info and switch to GitHub tab
        driver.find_element(By.ID, "title").click()
        driver.find_element(By.ID, "title").send_keys("test")
        driver.find_element(By.ID, "desc").send_keys("test")

        github_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "github-tab"))
        )
        github_tab.click()

        gh_url_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gh_url"))
        )
        gh_url_input.click()
        gh_url_input.send_keys("https://github.com/EGC-FoodHub/foodhub")

        gh_branch = driver.find_element(By.ID, "gh_branch")
        gh_branch.send_keys("invalid")

        import_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "import_repo_btn"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", import_btn)
        import_btn.click()
        wait_for_page_to_load(driver)

    finally:
        close_driver(driver)

