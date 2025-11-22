from app.modules.fooddataset.repositories import FooddatasetRepository
from core.services.BaseService import BaseService


class FooddatasetService(BaseService):
    def __init__(self):
        super().__init__(FooddatasetRepository())
