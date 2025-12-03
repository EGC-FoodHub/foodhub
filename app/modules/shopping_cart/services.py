from app.modules.shopping_cart.repositories import ShoppingCartRepository
from core.services.BaseService import BaseService


class ShoppingCartService(BaseService):
    def __init__(self):
        super().__init__(ShoppingCartRepository())
