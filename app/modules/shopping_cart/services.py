from app.modules.shopping_cart.repositories import ShoppingCartRepository
from core.services.BaseService import BaseService

from app.modules.dataset.repositories import DataSetRepository

from flask_login import current_user


class ShoppingCartService(BaseService):
    def __init__(self):
        super().__init__(ShoppingCartRepository())
        self.repository = ShoppingCartRepository()
        self.dataset_repository = DataSetRepository()

    def get_by_user(self, user_id):
        return self.repository.get_by_user(user_id)

    def create(self):
        return self.repository.create(user_id = current_user.id, data_sets = [])

    def add_to_cart(self, user_id, dataset_id):
        cart = self.get_by_user(user_id)
        if cart == None:
            cart = self.create()
        
        dataset = self.dataset_repository.get_by_id(dataset_id)
        cart.data_sets.append(dataset)
        self.repository.session.commit()
        
    def remove_from_cart(self, user_id, dataset_id):
        cart = self.get_by_user(user_id)
        dataset = self.dataset_repository.get_by_id(dataset_id)
        cart.data_sets.remove(dataset)
        self.repository.session.commit()

    def get_all_datasets_from_cart(self, user_id):
        self.repository.get_all_datasets_from_cart(user_id)




        
