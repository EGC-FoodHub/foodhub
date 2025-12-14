import re
import os
import pytest

from locust import HttpUser, TaskSet, task

from core.locust.common import get_csrf_token
from core.environment.host import get_host_for_locust_testing

pytestmark = pytest.mark.load


class FoodDatasetBehavior(TaskSet):
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
        else:
            print("Failed to find CSRF token")

        response = self.client.post(
            "/login", data={"email": "test_food@example.com", "password": "test1234", "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Failed to login. Status: {response.status_code}")

    @task()
    def list_datasets(self):
        response = self.client.get("/dataset/list")
        if response.status_code != 200:
            print(f"Dataset list failed: {response.status_code}")
            return

        # Extract all dataset IDs from the list page
        ids = re.findall(r'href="/dataset/(\d+)"', response.text)
        if ids:
            self.dataset_ids = list(set(ids))

    @task()
    def view_dataset_detail(self):
        if not self.dataset_ids:
            return  # Skip if no datasets found

        dataset_id = self.dataset_ids[0]
        self.client.get(f"/dataset/{dataset_id}")

    @task()
    def download_dataset(self):
        if not self.dataset_ids:
            return  # Skip

        dataset_id = self.dataset_ids[0]
        self.client.get(f"/dataset/download/{dataset_id}")

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


class FoodDatasetUser(HttpUser):
    tasks = [FoodDatasetBehavior]
    min_wait = 1000
    max_wait = 5000
    host = get_host_for_locust_testing()
