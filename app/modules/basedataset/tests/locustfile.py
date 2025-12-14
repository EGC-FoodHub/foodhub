import re

import pytest
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing

pytestmark = pytest.mark.load


class BasedatasetBehavior(TaskSet):
    def on_start(self):
        self.login()
        self.dataset_ids = []

    def login(self):
        # Fetch CSRF token
        response = self.client.get("/login")
        csrf_token = ""
        # Flexible regex
        token_match = re.search(r'name="csrf_token"[^>]+value="([^"]+)"', response.text)
        if not token_match:
            token_match = re.search(r'value="([^"]+)"[^>]+name="csrf_token"', response.text)

        if token_match:
            csrf_token = token_match.group(1)
            # print(f"CSRF Token: {csrf_token}")
        else:
            print("Failed to find CSRF token")

        response = self.client.post(
            "/login", data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Failed to login. Status: {response.status_code}")

    @task(3)
    def list_datasets(self):
        response = self.client.get("/dataset/list")
        if response.status_code != 200:
            print(f"Dataset list failed: {response.status_code}")
            return

        # Extract all dataset IDs from the list page
        # Look for href="/dataset/<id>" or href="/dataset/download/<id>"
        # The regex matches digits after /dataset/ or /dataset/download/
        # patterns might be: /dataset/123 or /dataset/download/123
        # We'll just grab from the view link: /dataset/123

        ids = re.findall(r'href="/dataset/(\d+)"', response.text)
        print(ids)
        if ids:
            self.dataset_ids = list(set(ids))  # unique IDs

    @task(1)
    def view_dataset_detail(self):
        if not self.dataset_ids:
            return  # Skip if no datasets found

        dataset_id = self.dataset_ids[0]
        self.client.get(f"/dataset/{dataset_id}")

    @task(1)
    def download_dataset(self):
        if not self.dataset_ids:
            return  # Skip

        dataset_id = self.dataset_ids[0]
        self.client.get(f"/dataset/download/{dataset_id}")


class BasedatasetUser(HttpUser):
    tasks = [BasedatasetBehavior]
    min_wait = 1000
    max_wait = 5000
    host = get_host_for_locust_testing()
