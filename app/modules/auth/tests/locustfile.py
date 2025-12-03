from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/signup", data={"email": fake.email(), "password": fake.password(), "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")

        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login", data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")


class Enable2FABehaviour(TaskSet):
    def on_start(self):
        self.ensure_logged_in()
        self.enter_activate_2fa_page()

    def ensure_logged_in(self):
        response = self.client.get("/login")
        if response.status_code == 200:
            print("Not logged in, redirecting to login")
            csrf_token = get_csrf_token(response)
            response = self.client.post(
                "/login", data={"email": "user2@example.com", "password": "1234", "csrf_token": csrf_token}
            )
            if response.status_code != 200:
                print(f"Login failed: {response.status_code}")

    @task
    def enter_activate_2fa_page(self):
        response = self.client.get("/enable_2fa")
        if response.status_code != 200:
            response.failure(f"Rendering failed: {response.status_code}")

    @task
    def add_failing_code(self):
        response = self.client.get("/enable_2fa")
        if response.status_code == 200:
            csrf_token = get_csrf_token(response)
            with self.client.post(
                "/enable_2fa", data={"code": 999999, "csrf_token": csrf_token}, catch_response=True
            ) as resp:
                if resp.status_code == 200 and "Incorrect 2FA code" in resp.text:
                    resp.success()
                elif resp.status_code == 302:
                    resp.failure("Invalid code was accepted - should have failed")
                else:
                    resp.failure(f"Unexpected response: {resp.status_code}")


class AuthUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior, Enable2FABehaviour]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
