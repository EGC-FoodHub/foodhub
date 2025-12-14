import time
import pytest
import uuid

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.selenium.common import initialize_driver
from core.environment.host import get_host_for_selenium_testing

from app import db, app
from app.modules.auth.models import User
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
from app.modules.basedataset.models import BaseAuthor, BasePublicationType
from datetime import datetime, timezone


def create_test_datasets_for_ranking(user):
    author = BaseAuthor(
        name="Selenium Test Author",
        affiliation="Test University"
    )
    db.session.add(author)
    db.session.flush()

    # Datasets idénticos
    datasets_identical = []
    for _ in range(2):
        meta = FoodDSMetaData(
            title="Selenium Apple Dataset",
            description="Dataset about apple quality and freshness",
            tags="apple,quality,fruit",
            publication_type=BasePublicationType.REPORT,
            dataset_doi=f"10.1234/selenium-{uuid.uuid4()}",
            authors=[author]
        )
        db.session.add(meta)
        db.session.flush()
        ds = FoodDataset(user_id=user.id, ds_meta_data=meta, created_at=datetime.now(timezone.utc))
        db.session.add(ds)
        datasets_identical.append(ds)

    # Dataset no idéntico (solo tag en común)
    meta_partial = FoodDSMetaData(
        title="Partial Apple Dataset",
        description="Only shares 'apple' tag",
        tags="apple",
        publication_type=BasePublicationType.REPORT,
        dataset_doi=f"10.1234/selenium-{uuid.uuid4()}",
        authors=[author]
    )
    db.session.add(meta_partial)
    db.session.flush()
    ds_partial = FoodDataset(user_id=user.id, ds_meta_data=meta_partial, created_at=datetime.now(timezone.utc))
    db.session.add(ds_partial)

    db.session.commit()

    for ds in datasets_identical + [ds_partial]:
        db.session.refresh(ds)
        db.session.refresh(ds.ds_meta_data)

    return datasets_identical, ds_partial


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

    def test_related_datasets_block_exists(self):
        self.login()

        dataset_doi = "10.1234/food-dataset-4"
        self.driver.get(f"{self.host}/doi/{dataset_doi}/")
        time.sleep(2)

        # Abrir primer dataset por DOI
        first_doi_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/doi/']")
        first_doi_link.click()
        time.sleep(2)

        related_title = self.driver.find_element(
            By.XPATH, "//h3[contains(text(), 'Related Datasets')]"
        )

        assert related_title.is_displayed()

    def test_related_datasets_ranking(self):
        with app.app_context():
            user = User.query.filter_by(email="user1@example.com").first()
            datasets_identical, ds_partial = create_test_datasets_for_ranking(user)
            ds1, ds2 = datasets_identical

        self.login()

        self.driver.get(f"{self.host}/doi/{ds1.ds_meta_data.dataset_doi}/")
        time.sleep(5)

        related_links = self.driver.find_elements(By.CSS_SELECTOR, ".card-body a[href*='/doi/']")
        related_titles = [link.text.strip() for link in related_links]

        assert related_titles[0] == ds2.ds_meta_data.title, "El dataset idéntico no aparece primero"

        # ds_partial también debería aparecer
        assert ds_partial.ds_meta_data.title in related_titles, "El dataset parcialmente relacionado no aparece"
        
