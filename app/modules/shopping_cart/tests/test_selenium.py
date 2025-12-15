import pytest
import time
from selenium.webdriver.common.by import By
from core.selenium.common import initialize_driver, close_driver
from core.environment.host import get_host_for_selenium_testing

pytestmark = pytest.mark.selenium


class TestAddDataset:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.host = get_host_for_selenium_testing()

    def teardown_method(self, method):
        close_driver(self.driver)

    def login(self):
        self.driver.get(f"{self.host}/login")
        self.driver.set_window_size(1024, 1132)
        time.sleep(1)
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        time.sleep(2)  

    def test_adddataset(self):
        self.login()
        self.driver.get(f"{self.host}/")
        self.driver.set_window_size(1024, 1132)
        time.sleep(2)
        self.driver.find_element(By.LINK_TEXT, "Add to cart").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(2) .btn:nth-child(3)").click()
        time.sleep(1)

    def test_deletedataset(self):
        self.login()
        self.driver.get(f"{self.host}/")
        self.driver.set_window_size(1024, 1132)
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR, ".feather-shopping-cart").click()
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Remove").click()
        time.sleep(1)

    def test_showdataset(self):
        self.login()
        self.driver.get(f"{self.host}/")
        self.driver.set_window_size(1024, 1132)
        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR, ".feather-shopping-cart").click()
        time.sleep(1)
