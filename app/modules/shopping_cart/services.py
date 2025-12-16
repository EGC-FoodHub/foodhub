from flask_login import current_user

from app.modules.fooddataset.repositories import FoodDatasetRepository
from app.modules.shopping_cart.repositories import ShoppingCartRepository
from app.modules.shopping_cart.models import DownloadRecord
from core.services.BaseService import BaseService


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

    '''

    APARTIR DE AQUI ES DE LA NUEVA IMPLEMENTACIÓN

    '''

    def checkout(self, user_id):
        """
        1. Copia items del carrito al historial.
        2. Guarda en DB.
        3. Vacía el carrito.
        """
        cart = self.get_by_user(user_id)
        if not cart or not cart.food_data_sets:
            return None

        # Crear registro de historial
        record = DownloadRecord(user_id=user_id)

        # Copiar datasets
        for dataset in cart.food_data_sets:
            record.datasets.append(dataset)

        self.repository.session.add(record)

        # Vaciar carrito tras la descarga
        cart.food_data_sets = []

        self.repository.session.commit()
        return record

    def get_history_by_user(self, user_id):
        return DownloadRecord.query.filter_by(user_id=user_id).order_by(DownloadRecord.created_at.desc()).all()

    def get_history_record_by_id(self, record_id, user_id):
        """
        Busca un registro específico, asegurando que pertenezca al usuario.
        """
        return DownloadRecord.query.filter_by(id=record_id, user_id=user_id).first()
