import os
import re

import pytest
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token

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
        zip_path = os.path.abspath("app/modules/fooddataset/food_examples.zip")

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

    @task
    def create_dataset_as_draft(self):
        """Crear un dataset como borrador"""
        response = self.client.get("/dataset/save_as_draft")
        csrf = get_csrf_token(response)
        if not csrf:
            print("⚠ CSRF token not found")
            return

        data = {
            "title": "Load Test Draft Dataset",
            "description": "Dataset de prueba en borrador",
            "publication_type": "dataset",
            "tags": "test,locust,draft",
            "csrf_token": csrf,
        }

        zip_path = os.path.abspath("app/modules/dataset/zip_examples/food.zip")
        if not os.path.exists(zip_path):
            print(f"⚠ ZIP not found: {zip_path}")
            return

        with open(zip_path, "rb") as f:
            files = {"food_models-0-filename": ("food.zip", f, "application/zip")}

            response = self.client.post("/dataset/save_as_draft", data=data, files=files)

        if response.status_code == 200:
            print("✔ Dataset creado como borrador correctamente")
            try:
                response_data = response.json()
                if "dataset_id" in response_data:
                    self.dataset_ids.append(response_data["dataset_id"])
            except Exception:
                pass
        else:
            print(f"⚠ Draft dataset creation failed: {response.status_code}")

    @task
    def publish_draft_dataset(self):
        """Publicar un dataset en borrador (convertir a DOI)"""
        if not self.dataset_ids:
            print("⚠ No dataset IDs available for publishing")
            return

        dataset_id = self.dataset_ids[0]

        response = self.client.get(f"/dataset/publish/{dataset_id}")
        csrf = get_csrf_token(response)
        if not csrf:
            print("⚠ CSRF token not found")
            return

        data = {
            "title": f"Published Dataset {dataset_id}",
            "description": "Dataset publicado con DOI",
            "publication_type": "dataset",
            "publication_doi": "10.5281/zenodo.example",
            "tags": "published,doi,test",
            "csrf_token": csrf,
        }

        response = self.client.post(
            f"/dataset/publish/{dataset_id}",
            data=data,
            catch_response=True
        )

        if response.status_code == 200:
            print(f"✔ Dataset {dataset_id} publicado correctamente")
            try:
                response_data = response.json()
                if response_data.get("message") == "Dataset published successfully":
                    response.success()
                else:
                    response.failure(f"Unexpected response: {response_data}")
            except Exception:
                response.failure("Invalid JSON response")
        else:
            print(f"⚠ Dataset publish failed: {response.status_code}")
            response.failure(f"Status code: {response.status_code}")

    @task
    def edit_doi_dataset(self):
        """Editar un dataset ya publicado con DOI"""
        if not self.dataset_ids:
            print("⚠ No dataset IDs available for editing")
            return

        dataset_id = self.dataset_ids[0]

        response = self.client.get(f"/dataset/edit/{dataset_id}")
        csrf = get_csrf_token(response)
        if not csrf:
            print("⚠ CSRF token not found")
            return

        data = {
            "title": f"Edited Dataset {dataset_id}",
            "description": "Dataset editado con nueva descripción",
            "publication_type": "dataset",
            "publication_doi": "10.5281/zenodo.example.v2",
            "tags": "edited,test,updated",
            "csrf_token": csrf,
        }

        file_path = os.path.abspath("app/modules/dataset/food_examples/test.food")

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                files = {"food_models-0-filename": ("test.food", f, "application/octet-stream")}
                response = self.client.post(
                    f"/dataset/edit/{dataset_id}",
                    data=data,
                    files=files,
                    catch_response=True
                )
        else:
            response = self.client.post(
                f"/dataset/edit/{dataset_id}",
                data=data,
                catch_response=True
            )

        if response.status_code in [200, 302]:
            print(f"✔ Dataset {dataset_id} editado correctamente")
            response.success()
        else:
            print(f"⚠ Dataset edit failed: {response.status_code}")
            response.failure(f"Status code: {response.status_code}")


class FoodDatasetUser(HttpUser):
    tasks = [FoodDatasetBehavior]
    min_wait = 1000
    max_wait = 5000
    host = get_host_for_locust_testing()
