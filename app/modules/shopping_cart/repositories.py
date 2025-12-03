from app.modules.shopping_cart.models import ShoppingCart
from core.repositories.BaseRepository import BaseRepository


class ShoppingCartRepository(BaseRepository):
    def __init__(self):
        super().__init__(ShoppingCart)
        
    def get_by_user(self, user_id):
        return ShoppingCart.query.filter_by(user_id=user_id).first()

    def get_all_datasets_from_cart(self, user_id):
        return ShoppingCart.query.filter_by(user_id=user_id).first().data_sets
