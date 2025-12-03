from app.modules.shopping_cart.models import ShoppingCart
from core.repositories.BaseRepository import BaseRepository


class ShoppingCartRepository(BaseRepository):
    def __init__(self):
        super().__init__(ShoppingCart)
