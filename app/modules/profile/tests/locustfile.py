from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing


class ProfileBehavior(TaskSet):
    def on_start(self):
        """Se ejecuta al inicio de cada usuario virtual"""
        self.login()

    def login(self):
        """Login inicial"""
        response = self.client.post("/login", data={
            "email": "user1@example.com",
            "password": "1234"
        })
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")

    @task(2)
    def view_profile(self):
        """Simula abrir perfil de usuario"""
        response = self.client.get("/profile/18")
        if response.status_code != 200:
            print(f"View profile failed: {response.status_code}")

    @task(1)
    def edit_profile(self):
        """Simula editar perfil de usuario"""
        response = self.client.post("/profile/edit", data={
            "name": "LocustTestName",
            "surname": "LocustTestSurname",
            "affiliation": "LocustClub",
            "orcid": "0000-0000-0000-0000"
        })
        if response.status_code != 200:
            print(f"Edit profile failed: {response.status_code}")

    @task(1)
    def list_datasets(self):
        """Simula listar datasets del usuario"""
        response = self.client.get("/dataset/list")
        if response.status_code != 200:
            print(f"List datasets failed: {response.status_code}")

class ProfileUser(HttpUser):
    tasks = [ProfileBehavior]
    min_wait = 5000  
    max_wait = 9000  
    host = get_host_for_locust_testing()
