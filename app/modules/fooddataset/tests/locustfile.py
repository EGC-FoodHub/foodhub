import random
import re
import time
from datetime import datetime, timedelta

from locust import HttpUser, TaskSet, between, events, task

from core.environment.host import get_host_for_locust_testing


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

    @task(3)
    def list_datasets(self):
        response = self.client.get("/dataset/list")
        if response.status_code != 200:
            print(f"Dataset list failed: {response.status_code}")
            return

        # Extract all dataset IDs from the list page
        ids = re.findall(r'href="/dataset/(\d+)"', response.text)
        if ids:
            self.dataset_ids = list(set(ids))

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
                except:
                    response.failure("No es JSON válido")
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
