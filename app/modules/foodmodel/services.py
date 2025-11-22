from app.modules.foodmodel.repositories import FoodModelMetaDataRepository, FoodModelRepository
from app.modules.hubfile.services import HubfileService
from core.services.BaseService import BaseService


class FoodModelService(BaseService):
    def __init__(self):
        super().__init__(FoodModelRepository())
        self.hubfile_service = HubfileService()

    def total_food_model_views(self) -> int:
        return self.hubfile_service.total_hubfile_views()

    def total_food_model_downloads(self) -> int:
        return self.hubfile_service.total_hubfile_downloads()

    def count_food_models(self):
        return self.repository.count_food_models()

    class FoodModelMetaDataService(BaseService):
        def __init__(self):
            super().__init__(FoodModelMetaDataRepository())
