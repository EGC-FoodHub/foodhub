import logging
import os

import pytest
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token

pytestmark = pytest.mark.load

logger = logging.getLogger(__name__)


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
        if upload.status_code in [200, 302]:
            print("✔ ZIP cargado correctamente")
        else:
            print(f"⚠ ZIP upload failed: {upload.status_code}")

    @task
    def upload_local_file(self):
        """Subida de archivo local tipo (.food)"""
        # 1. GET para obtener CSRF
        response = self.client.get("/dataset/upload")
        csrf = get_csrf_token(response)
        if not csrf:
            print("⚠ CSRF token not found")
            return

        # 2. Datos del formulario
        data = {
            "title": "Load Test Local File",
            "description": "Prueba carga concurrente local file",
            "csrf_token": csrf,
        }

        # 3. Archivo local de prueba
        file_path = os.path.abspath("app/modules/dataset/food_examples/test.food")
        if not os.path.exists(file_path):
            print(f"⚠ Local file not found: {file_path}")
            return

        with open(file_path, "rb") as f:
            files = {"file": ("test.food", f, "application/octet-stream")}

            # 4. POST real para subir el archivo
            upload = self.client.post("/dataset/file/upload", data=data, files=files)

        # 5. Validación simple
        if upload.status_code in [200, 302]:
            print("✔ Local file cargado correctamente")
        else:
            print(f"⚠ Local file upload failed: {upload.status_code}")

    @task
    def upload_github(self):
        """Trigger an import from a GitHub repository using form fields."""
        # 1. GET para obtener CSRF (igual que upload_zip)
        response = self.client.get("/dataset/upload")
        try:
            csrf = get_csrf_token(response)
        except Exception:
            csrf = None

        if not csrf:
            print("⚠ CSRF token not found")
            return

        # The server endpoint expects either 'repo' (owner/repo) or 'zip_url'
        repo = "EGC-FoodHub/foodhub"
        data = {"repo": repo, "branch": "main", "csrf_token": csrf}

        with self.client.post("/dataset/file/upload_github", data=data) as r:
            # mirror upload_zip validation: accept 200 or 302
            if r.status_code in [200, 302]:
                print("✔ GitHub importado correctamente")
            else:
                print(f"⚠ GitHub import failed: {r.status_code}")


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
