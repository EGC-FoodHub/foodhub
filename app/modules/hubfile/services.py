import logging
import os

from app.modules.auth.models import User
from app.modules.fooddataset.models import FoodDataset
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class HubfileService(BaseService):
    def __init__(self):
        super().__init__(HubfileRepository())
        self.hubfile_view_record_repository = HubfileViewRecordRepository()
        self.hubfile_download_record_repository = HubfileDownloadRecordRepository()

    def get_owner_user_by_hubfile(self, hubfile: Hubfile) -> User:
        """
        Obtiene el usuario dueño del archivo navegando las relaciones.
        """
        if hubfile.food_model and hubfile.food_model.dataset:
            return hubfile.food_model.dataset.user
        return None

    def get_dataset_by_hubfile(self, hubfile: Hubfile) -> FoodDataset:
        """
        Obtiene el dataset al que pertenece el archivo.
        """
        if hubfile.food_model:
            return hubfile.food_model.dataset
        return None

    def get_path_by_hubfile(self, hubfile: Hubfile) -> str:
        """
        Construye la ruta física absoluta del archivo.
        """
        dataset = self.get_dataset_by_hubfile(hubfile)

        if not dataset:
            logger.error(f"Hubfile {hubfile.id} is orphaned (no linked dataset)")
            return None

        user = dataset.user

        base_dir = uploads_folder_name()

        path = os.path.join(base_dir, f"user_{user.id}", f"dataset_{dataset.id}", hubfile.name)

        return path

    def total_hubfile_views(self) -> int:
        return self.hubfile_view_record_repository.total_hubfile_views()

    def total_hubfile_downloads(self) -> int:
        return self.hubfile_download_record_repository.total_hubfile_downloads()


class HubfileDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(HubfileDownloadRecordRepository())
