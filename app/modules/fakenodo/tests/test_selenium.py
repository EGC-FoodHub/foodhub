import os
import time

import pytest
from selenium.webdriver.common.by import By

from app import app, db
from app.modules.basedataset.models import BaseAuthor, BaseDSViewRecord
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.selenium


class TestDatasetRecommendations:

    def setup_method(self, method):
        self.driver = initialize_driver()
        self.host = get_host_for_selenium_testing()

    def teardown_method(self, method):
        self.driver.quit()

    def login(self):
        self.driver.get(f"{self.host}/")
        self.driver.set_window_size(1200, 900)

        self.driver.find_element(By.LINK_TEXT, "Login").click()

        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")

        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")

        self.driver.find_element(By.ID, "submit").click()
        time.sleep(2)

    def create_test_datasets_fakenodo(self):
        self.driver.set_window_size(1854, 1048)
        self.driver.find_element(By.ID, "title").click()
        self.driver.find_element(By.ID, "title").send_keys("FakenodoTesting")

        self.driver.find_element(By.ID, "desc").click()
        self.driver.find_element(By.ID, "desc").send_keys("FakenodoTesting")

        dropdown = self.driver.find_element(By.ID, "publication_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Book']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(3)").click()

        self.driver.find_element(By.ID, "tags").click()
        self.driver.find_element(By.ID, "tags").send_keys("fakenodo")
        
        upload_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../..", "fooddataset/food_examples/espinacas.food")
        )

        file_input = self.driver.find_element(By.CSS_SELECTOR, "input.dz-hidden-input")

        self.driver.execute_script(
            "arguments[0].style.display = 'block'; arguments[0].style.opacity = '1'; arguments[0].style.visibility = \
                'visible';", file_input)

        file_input.send_keys(upload_file)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dz-success"))
        )

        self.driver.find_element(By.ID, "agreeCheckbox").click()
        self.driver.find_element(By.ID, "upload_button").click()
        time.sleep(2)

    def test_related_datasets_block_exists(self):
        try:
            self.login()

            upload_dataset = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/dataset/upload']")
            upload_dataset.click()
            time.sleep(1)
            self.create_test_datasets_fakenodo()

            dataset_DOI = self.driver.find_element(By.CSS_SELECTOR, "a[href^='/doi/fakenodo']")

            assert dataset_DOI.is_displayed()

        finally:
            with app.app_context():
                metadatas = FoodDSMetaData.query.filter_by(title="FakenodoTesting").all()

                for meta in metadatas:
                    ds_id = meta.id

                    # 2. Delete "Leaf" records (Foreign Key dependencies)
                    # Delete Authors pointing to this metadata
                    db.session.query(BaseAuthor).filter_by(food_ds_meta_data_id=meta.id).delete()

                    # Delete View Records pointing to this dataset
                    db.session.query(BaseDSViewRecord).filter_by(dataset_id=ds_id).delete()

                    # 3. Delete the Metadata
                    db.session.delete(meta)

                    # 4. Finally, delete the parent Dataset
                    dataset = FoodDataset.query.get(ds_id)
                    if dataset:
                        db.session.delete(dataset)

                db.session.commit()
