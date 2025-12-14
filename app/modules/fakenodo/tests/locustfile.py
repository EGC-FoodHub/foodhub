from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class FakenodoBehavior(TaskSet):

    def on_start(self):
        self.test_index()
        self.create_record()

    @task
    def test_index(self):
        """GET /fakenodo"""
        self.client.get("/fakenodo")

    @task
    def create_record(self):
        """POST /fakenodo/records"""
        payload = {
            "metadata": {"title": "Locust Test"},
            "files": [],
        }

        response = self.client.post("/fakenodo/records", json=payload)
        if response.status_code == 201:
            self.record_id = response.json().get("id")
        else:
            self.record_id = None

    @task
    def get_record(self):
        """GET the record created"""
        if not hasattr(self, "record_id") or not self.record_id:
            return

        self.client.get(f"/fakenodo/records/{self.record_id}")

    @task
    def publish_record(self):
        """POST /records/<id>/publish"""
        if not hasattr(self, "record_id") or not self.record_id:
            return

        self.client.post(f"/fakenodo/records/{self.record_id}/publish")

    @task
    def add_files(self):
        """POST /records/<id>/files"""
        if not hasattr(self, "record_id") or not self.record_id:
            return

        payload = {"files": ["file1.txt", "file2.json"]}
        self.client.post(f"/fakenodo/records/{self.record_id}/files", json=payload)
    


class FakenodoUser(HttpUser):
    tasks = [FakenodoBehavior]
    min_wait = 3000
    max_wait = 6000
    host = get_host_for_locust_testing()