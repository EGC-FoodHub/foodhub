from sqlalchemy import func
from app.modules.foodmodel.models import FoodMetaData, FoodModel
from core.repositories.BaseRepository import BaseRepository



class FoodModelRepository(BaseRepository):
    def __init__(self):
        super().__init__(FoodModel)

    def count_food_models(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0
    

class FoodModelMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(FoodMetaData)

