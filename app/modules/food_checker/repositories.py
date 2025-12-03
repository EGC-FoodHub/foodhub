from app.modules.food_checker.models import FoodChecker
from core.repositories.BaseRepository import BaseRepository


class FoodCheckerRepository(BaseRepository):
    def __init__(self):
        super().__init__(FoodChecker)
