import pytest
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing

pytestmark = pytest.mark.load


class RecommendationBehavior(TaskSet):

    @task
    def test_recommendation_loading(self):
        """GET /doi/10.1234/food-dataset-4/"""
        self.client.get("/doi/10.1234/food-dataset-4/")


class RecommendationUser(HttpUser):
    tasks = [RecommendationBehavior]
    min_wait = 3000
    max_wait = 6000
    host = get_host_for_locust_testing()
