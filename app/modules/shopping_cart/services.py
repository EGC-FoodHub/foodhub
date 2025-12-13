from app.modules.shopping_cart.repositories import ShoppingCartRepository
from core.services.BaseService import BaseService

from app.modules.fooddataset.repositories import FoodDatasetRepository

from flask_login import current_user


class ShoppingCartService(BaseService):
    def __init__(self):
        super().__init__(ShoppingCartRepository())
        self.repository = ShoppingCartRepository()
        self.dataset_repository = FoodDatasetRepository()

    def get_by_user(self, user_id):
        return self.repository.get_by_user(user_id)

    def show_by_user(self, user_id):
        cart = self.get_by_user(user_id)
        if cart is None:
            cart = self.create()
        return cart

    def create(self):
        return self.repository.create(user_id=current_user.id, food_data_sets=[])

    def add_to_cart(self, user_id, food_dataset_id):
        cart = self.get_by_user(user_id)
        if cart is None:
            cart = self.create()

        food_dataset = self.dataset_repository.get_by_id(food_dataset_id)
        cart.food_data_sets.append(food_dataset)
        self.repository.session.commit()

    def remove_from_cart(self, user_id, food_dataset_id):
        cart = self.get_by_user(user_id)
        food_dataset = self.dataset_repository.get_by_id(food_dataset_id)
        cart.food_data_sets.remove(food_dataset)
        self.repository.session.commit()

    def get_all_datasets_from_cart(self, user_id):
        self.repository.get_all_datasets_from_cart(user_id)
