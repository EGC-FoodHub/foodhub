import pytest
from locust import HttpUser, between, task

pytestmark = pytest.mark.load


class FoodCheckerUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(1, 5)

    @task
    def check_dataset(self):
        # Assuming dataset 1 exists, or we might get 404 which is fine for load testing the path
        self.client.get("/api/food_checker/check/dataset/1")

    @task
    def check_file(self):
        # Assuming file 1 exists
        self.client.get("/api/food_checker/check/file/1")
