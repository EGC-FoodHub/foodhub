from app.modules.fooddataset.models import Fooddataset
from core.repositories.BaseRepository import BaseRepository


class FooddatasetRepository(BaseRepository):
    def __init__(self):
        super().__init__(Fooddataset)
