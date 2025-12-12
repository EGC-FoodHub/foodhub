import os

import pytest
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token

pytestmark = pytest.mark.load


class DatasetBehavior(TaskSet):
    """Dataset ZIP upload load testing behavior"""

    def on_start(self):
        self.upload_zip()

    @task
    def upload_zip(self):
        # 1. GET para obtener CSRF
        response = self.client.get("/dataset/upload")
        csrf = get_csrf_token(response)
        if not csrf:
            print("⚠ CSRF token not found")
            return

        # 2. Datos del formulario
        data = {
            "title": "Load Test ZIP",
            "description": "Carga concurrente",
            "csrf_token": csrf,
        }

        # 3. ZIP de prueba
        zip_path = os.path.abspath("app/modules/dataset/zip_examples/food.zip")

        if not os.path.exists(zip_path):
            print(f"⚠ ZIP not found: {zip_path}")
            return

        with open(zip_path, "rb") as f:
            files = {"zip_file": ("test.zip", f, "application/zip")}

            # 4. POST real para subir el ZIP
            upload = self.client.post("/dataset/upload", data=data, files=files)

        # 5. Validación simple tipo Hubfile
        if upload.status_code not in [200, 302]:
            print(f"⚠ ZIP upload failed: {upload.status_code}")


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
