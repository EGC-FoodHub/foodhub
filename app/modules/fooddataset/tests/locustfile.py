import os
import random
import re
import time
from datetime import datetime

import pytest
from locust import HttpUser, TaskSet, events, task

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

        response = self.client.post(f"/dataset/publish/{dataset_id}", data=data, catch_response=True)

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
                response = self.client.post(f"/dataset/edit/{dataset_id}", data=data, files=files, catch_response=True)
        else:
            response = self.client.post(f"/dataset/edit/{dataset_id}", data=data, catch_response=True)

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


class TrendingLoadTestBehavior(TaskSet):

    def on_start(self):
        """Se ejecuta cuando un usuario virtual inicia"""
        self.login()
        self.dataset_ids = []
        self.last_trending_data = []

        # Para tracking de métricas personalizadas
        self.start_time = time.time()

    def on_stop(self):
        """Se ejecuta cuando un usuario virtual termina"""
        duration = time.time() - self.start_time
        print(f"Usuario completó sesión después de {duration:.2f} segundos")

    def login(self):
        """Login básico para rutas que requieren autenticación"""
        try:
            # Primero obtenemos la página de login para el CSRF token
            response = self.client.get("/login")
            csrf_token = ""

            # Buscar CSRF token en diferentes formatos
            patterns = [
                r'name="csrf_token"[^>]+value="([^"]+)"',
                r'value="([^"]+)"[^>]+name="csrf_token"',
                r'csrf-token[^>]+content="([^"]+)"',
                r'<input[^>]+id="csrf_token"[^>]+value="([^"]+)"',
            ]

            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    csrf_token = match.group(1)
                    break

            # Datos de login (ajusta según tu aplicación)
            login_data = {
                "email": "test@example.com",
                "password": "password123",
                "csrf_token": csrf_token,
                "remember": "y",
            }

            # Intentar login
            response = self.client.post("/login", data=login_data)

            if response.status_code in [200, 302]:
                print("Login exitoso")
                return True
            else:
                print(f"Login falló con código: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error en login: {e}")
            return False

    @task(15)  # Muy alta frecuencia - API de trending principal
    def get_trending_api(self):
        """Endpoint principal de trending (ajusta la ruta según tu app)"""
        with self.client.get(
            "/api/datasets/trending",  # Ruta de ejemplo
            name="API - Trending datasets",
            catch_response=True,
            params={"days": random.choice([7, 30]), "limit": random.randint(5, 50)},
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and isinstance(data, list):
                        self.last_trending_data = data
                        # Métrica personalizada para éxito
                        events.request.fire(
                            request_type="GET",
                            name="Trending API Success",
                            response_time=response.elapsed.total_seconds() * 1000,
                            response_length=len(response.content),
                        )
                        response.success()
                    else:
                        response.failure("Respuesta vacía o no es lista")
                except Exception as e:
                    response.failure(f"Error JSON: {str(e)}")
            else:
                response.failure(f"Status {response.status_code}")

    @task(12)  # Alta frecuencia - Página web de trending
    def view_trending_page(self):
        """Página HTML de trending"""
        with self.client.get(
            "/datasets/trending", name="Página - Trending", catch_response=True  # Ruta de ejemplo
        ) as response:
            if response.status_code == 200:
                # Verificar que es una página HTML con contenido
                if "text/html" in response.headers.get("Content-Type", "") and "trending" in response.text.lower():
                    response.success()
                else:
                    response.failure("No es HTML o no contiene 'trending'")
            else:
                response.failure(f"Status {response.status_code}")

    @task(10)  # Alta frecuencia - Estadísticas generales
    def get_statistics(self):
        """Endpoint de estadísticas (si existe)"""
        with self.client.get(
            "/api/statistics", name="API - Statistics", catch_response=True  # Ruta de ejemplo
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Verificar estructura básica
                    if isinstance(data, dict) and len(data) > 0:
                        response.success()
                    else:
                        response.failure("Respuesta vacía o no es dict")
                except Exception as e:
                    response.failure(f"Error JSON: {str(e)}")
            else:
                response.failure(f"Status {response.status_code}")

    @task(8)  # Frecuencia media - Más vistos
    def get_most_viewed(self):
        """Dataset más vistos"""
        with self.client.get(
            "/api/datasets/most-viewed",  # Ruta de ejemplo
            name="API - Most viewed",
            catch_response=True,
            params={"limit": random.randint(5, 20)},
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(8)  # Frecuencia media - Más descargados
    def get_most_downloaded(self):
        """Dataset más descargados"""
        with self.client.get(
            "/api/datasets/most-downloaded",  # Ruta de ejemplo
            name="API - Most downloaded",
            catch_response=True,
            params={"limit": random.randint(5, 20)},
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(6)  # Frecuencia media - Listar datasets (para obtener IDs)
    def list_datasets(self):
        """Lista general de datasets para obtener IDs"""
        with self.client.get(
            "/datasets", name="Página - List datasets", catch_response=True  # Ruta de ejemplo
        ) as response:
            if response.status_code == 200:
                # Extraer IDs de datasets de la página
                ids = re.findall(r"/dataset/(\d+)", response.text)
                if ids:
                    self.dataset_ids = list(set(ids))[:10]  # Guardar hasta 10 IDs
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(5)  # Frecuencia media - Ver detalle de dataset
    def view_dataset_detail(self):
        """Ver un dataset específico (incrementa vistas)"""
        if self.dataset_ids or self.last_trending_data:
            # Usar IDs de la lista o de trending
            if self.dataset_ids:
                dataset_id = random.choice(self.dataset_ids)
            else:
                # Extraer ID del trending data si está disponible
                dataset = random.choice(self.last_trending_data[:5]) if self.last_trending_data else None
                dataset_id = str(dataset.get("id")) if dataset else None

            if dataset_id:
                with self.client.get(
                    f"/dataset/{dataset_id}", name="Página - Dataset detail", catch_response=True  # Ruta de ejemplo
                ) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Status {response.status_code}")

    @task(4)  # Frecuencia media - Registrar vista (API)
    def register_view(self):
        """Registrar una vista vía API (si existe)"""
        if self.dataset_ids or self.last_trending_data:
            if self.dataset_ids:
                dataset_id = random.choice(self.dataset_ids)
            else:
                dataset = random.choice(self.last_trending_data[:5]) if self.last_trending_data else None
                dataset_id = str(dataset.get("id")) if dataset else None

            if dataset_id:
                with self.client.post(
                    f"/api/dataset/{dataset_id}/view",  # Ruta de ejemplo
                    name="API - Register view",
                    catch_response=True,
                    json={"timestamp": datetime.now().isoformat()},
                ) as response:
                    if response.status_code in [200, 201, 204]:
                        response.success()
                    else:
                        response.failure(f"Status {response.status_code}")

    @task(3)  # Baja frecuencia - Estadísticas de un dataset
    def get_dataset_stats(self):
        """Estadísticas específicas de un dataset"""
        if self.dataset_ids or self.last_trending_data:
            if self.dataset_ids:
                dataset_id = random.choice(self.dataset_ids)
            else:
                dataset = random.choice(self.last_trending_data[:5]) if self.last_trending_data else None
                dataset_id = str(dataset.get("id")) if dataset else None

            if dataset_id:
                with self.client.get(
                    f"/api/dataset/{dataset_id}/stats",  # Ruta de ejemplo
                    name="API - Dataset stats",
                    catch_response=True,
                ) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Status {response.status_code}")

    @task(2)  # Baja frecuencia - Homepage (puede incluir trending)
    def view_homepage(self):
        """Homepage que podría mostrar contenido trending"""
        with self.client.get("/", name="Página - Home", catch_response=True) as response:  # Homepage
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)  # Baja frecuencia - Simular flujo completo
    def simulate_user_session(self):
        """Simular una sesión completa de usuario interesado en trending"""
        # 1. Ver homepage
        self.client.get("/", name="Flujo - Home")
        self.wait()

        # 2. Ver página de trending
        self.client.get("/datasets/trending", name="Flujo - Trending page")
        self.wait()

        # 3. Obtener datos de trending via API
        self.client.get("/api/datasets/trending", params={"days": 7, "limit": 10}, name="Flujo - Trending API")
        self.wait()

        # 4. Ver detalle de un dataset trending
        if self.last_trending_data:
            dataset = random.choice(self.last_trending_data[:3])
            dataset_id = dataset.get("id")
            if dataset_id:
                self.client.get(f"/dataset/{dataset_id}", name="Flujo - Dataset detail")

        # 5. Registrar una vista
        if self.last_trending_data:
            dataset = random.choice(self.last_trending_data[:3])
            dataset_id = dataset.get("id")
            if dataset_id:
                self.client.post(
                    f"/api/dataset/{dataset_id}/view",
                    json={"timestamp": datetime.now().isoformat()},
                    name="Flujo - Register view",
                )

    @task(1)  # Muy baja frecuencia - Buscar datasets
    def search_datasets(self):
        """Búsqueda que podría ordenar por trending"""
        search_terms = ["food", "recipe", "nutrition", "health", "data"]
        term = random.choice(search_terms)

        with self.client.get(
            "/datasets/search",  # Ruta de ejemplo
            name="Página - Search",
            catch_response=True,
            params={"q": term, "sort": random.choice(["trending", "recent", "popular"])},
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
