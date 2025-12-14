import pytest
from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing

pytestmark = pytest.mark.load


class ShoppingCartBehavior(TaskSet):
    def on_start(self):
        self.index()

    @task(3)
    def index(self):
        """Prueba de la página principal del carrito"""
        response = self.client.get("/shopping_cart")
        if response.status_code != 200:
            print(f"ShoppingCart index failed: {response.status_code}")

    @task(2)
    def add_dataset(self):
        """Prueba de añadir un dataset al carrito"""
        dataset_id = 1
        response = self.client.get(f"/shopping_cart/add/{dataset_id}")
        if response.status_code != 200 and response.status_code != 302:
            print(f"Add dataset failed: {response.status_code}")

    @task(1)
    def remove_dataset(self):
        """Prueba de eliminar un dataset del carrito"""
        dataset_id = 1
        response = self.client.get(f"/shopping_cart/remove/{dataset_id}")
        if response.status_code != 200:
            print(f"Remove dataset failed: {response.status_code}")


class ShoppingCartUser(HttpUser):
    tasks = [ShoppingCartBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
