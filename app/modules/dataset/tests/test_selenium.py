import os
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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


@pytest.mark.selenium
def test_upload_valid_food_zip():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Abrir login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Completar login
        email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
        password_field = driver.find_element(By.ID, "password")
        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        driver.find_element(By.ID, "submit").click()
        wait_for_page_to_load(driver)
        time.sleep(1)

        # Ir a upload dataset
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Upload dataset"))).click()
        wait_for_page_to_load(driver)

        # Completar info del dataset
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "title"))).send_keys("Test Food Dataset")
        driver.find_element(By.ID, "desc").send_keys("Descripción de prueba")

        # Subir ZIP con ruta absoluta correcta
        zip_path = os.path.abspath("app/modules/dataset/zip_examples/food.zip")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "zip-tab"))).click()

        zip_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "zip_input")))
        zip_input.send_keys(zip_path)

        upload_zip_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_zip_btn")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_zip_btn)
        upload_zip_btn.click()

        # Aceptar términos
        agree_checkbox = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "agreeCheckbox")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agree_checkbox)
        agree_checkbox.click()

        # Botón final subir dataset
        upload_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_button")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_btn)
        upload_btn.click()

        wait_for_page_to_load(driver)
        time.sleep(1)

        # Validar que la subida funcionó
        assert driver.current_url == f"{host}/dataset/list"
        print("Subida de .food vía ZIP completada correctamente!")

    finally:
        close_driver(driver)


@pytest.mark.selenium
def test_upload_zip_no_file():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Abrir la página principal
        driver.get(host)
        wait_for_page_to_load(driver)
        driver.set_window_size(1124, 1064)

        # Ir a login
        login_nav = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-link:nth-child(1)"))
        )
        login_nav.click()
        wait_for_page_to_load(driver)

        # Completar login
        email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
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

        # Cambiar a la pestaña ZIP
        zip_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "zip-tab")))
        zip_tab.click()

        # Click en el botón de subir ZIP sin seleccionar archivo
        upload_zip_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_zip_btn")))
        upload_zip_btn.click()
        wait_for_page_to_load(driver)
        time.sleep(1)

        # Validación: verificar que aparece un mensaje de error
        error_message = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#zip_status span.text-danger"))
        )
        assert "Seleccione un archivo" in error_message.text or error_message.is_displayed()

        print("Test de subir ZIP sin archivo con login validado correctamente!")

    finally:
        close_driver(driver)


@pytest.mark.selenium
def test_upload_zip_with_non_food_files():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Abrir página y login
        driver.get(host)
        wait_for_page_to_load(driver)
        driver.set_window_size(1124, 1064)

        # Click en login
        login_nav = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-link:nth-child(1)"))
        )
        login_nav.click()

        email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
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

        # Completar título y descripción
        driver.find_element(By.ID, "title").send_keys("Test ZIP with .uvl")
        driver.find_element(By.ID, "desc").send_keys("Testing invalid file in ZIP")

        # Cambiar a la pestaña ZIP
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "zip-tab"))).click()

        # Seleccionar ZIP que contiene solo .uvl
        zip_path = os.path.abspath("app/modules/dataset/zip_examples/uvl.zip")
        zip_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "zip_input")))
        zip_input.send_keys(zip_path)

        # Click en Upload ZIP
        upload_zip_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_zip_btn")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_zip_btn)
        driver.execute_script("arguments[0].click();", upload_zip_btn)

        # Validar mensaje de advertencia
        warning_locator = (By.CSS_SELECTOR, "#zip_status span.text-warning")
        WebDriverWait(driver, 5).until(
            EC.text_to_be_present_in_element(warning_locator, "No .food files found in the ZIP")
        )
        warning_message = driver.find_element(*warning_locator)
        assert "No .food files found in the ZIP" in warning_message.text
        print("Mensaje de advertencia detectado correctamente para ZIP con .uvl.")

    finally:
        close_driver(driver)


@pytest.mark.selenium
def test_upload_zip_no_title_no_description():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Abrir página y login
        driver.get(host)
        wait_for_page_to_load(driver)
        driver.set_window_size(1176, 1063)

        # Click en Login
        login_nav = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Login")))
        login_nav.click()

        email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
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

        # Cambiar a la pestaña ZIP
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "zip-tab"))).click()

        # Seleccionar ZIP válido
        zip_path = os.path.abspath("app/modules/dataset/zip_examples/food.zip")
        zip_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "zip_input")))
        zip_input.send_keys(zip_path)

        # Click en Upload ZIP
        upload_zip_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_zip_btn")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_zip_btn)
        driver.execute_script("arguments[0].click();", upload_zip_btn)

        # Aceptar checkbox y click en botón de subida sin completar título/desc
        agree_checkbox = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "agreeCheckbox")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agree_checkbox)
        agree_checkbox.click()

        upload_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "upload_button")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_btn)
        driver.execute_script("arguments[0].click();", upload_btn)

        # ===========================
        # Validar mensajes de error
        # ===========================
        error_container = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "upload_error")))
        error_messages = error_container.find_elements(By.TAG_NAME, "p")
        texts = [p.text for p in error_messages]

        assert any("title must be of minimum length 3" in t for t in texts)
        assert any("description must be of minimum length 3" in t for t in texts)

        print("Errores de título y descripción detectados correctamente:", texts)

    finally:
        close_driver(driver)
