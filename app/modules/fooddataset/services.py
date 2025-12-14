import hashlib
import logging
import os
import shutil
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from app.modules.basedataset.services import BaseDatasetService
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
from app.modules.fooddataset.repositories import FoodDatasetRepository
from app.modules.foodmodel.models import FoodMetaData, FoodModel
from app.modules.hubfile.repositories import HubfileRepository

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class FoodDatasetService(BaseDatasetService):
    def __init__(self):
        super().__init__(repository=FoodDatasetRepository())
        self.hubfile_repository = HubfileRepository()
        self.author_repository = self.author_repository
        self.dsmetadata_repository = self.dsmetadata_repository

    def get_synchronized(self, current_user_id: int):
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int):
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int):
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_unsynchronized_datasets(self):
        return self.repository.count_unsynchronized_datasets()

    def get_uvlhub_doi(self, dataset: FoodDataset) -> str:
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"

    def create_from_form(self, form, current_user) -> FoodDataset:
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }

        try:
            logger.info(f"Creating FoodDSMetaData...: {form.get_dsmetadata()}")

            dsmetadata = FoodDSMetaData(**form.get_dsmetadata())

            self.dsmetadata_repository.session.add(dsmetadata)
            self.dsmetadata_repository.session.flush()

            for author_data in [main_author] + form.get_authors():
                self.author_repository.create(commit=False, food_ds_meta_data_id=dsmetadata.id, **author_data)

            dataset = self.create(commit=False, user_id=current_user.id)

            dataset.ds_meta_data_id = dsmetadata.id

            for food_model_form in form.food_models:
                filename = food_model_form.filename.data

                food_metadata = FoodMetaData(**food_model_form.get_food_metadata())
                self.repository.session.add(food_metadata)
                self.repository.session.flush()

                for author_data in food_model_form.get_authors():
                    self.author_repository.create(commit=False, food_meta_data_id=food_metadata.id, **author_data)

                food_model = FoodModel(dataset=dataset, food_meta_data_id=food_metadata.id)

                file_path = os.path.join(current_user.temp_folder(), filename)
                checksum, size = calculate_checksum_and_size(file_path)

                hubfile = self.hubfile_repository.create(
                    commit=False, name=filename, checksum=checksum, size=size, food_model=food_model
                )

                food_model.files.append(hubfile)

            self.repository.session.commit()

            self._move_dataset_files(dataset, current_user)

        except Exception as exc:
            logger.error(f"Exception creating food dataset: {exc}")
            self.repository.session.rollback()
            raise exc

        return dataset

    def _move_dataset_files(self, dataset, current_user):
        """Mueve los archivos físicos del directorio temporal al final."""
        source_dir = current_user.temp_folder()
        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")
        os.makedirs(dest_dir, exist_ok=True)

        for food_model in dataset.files:
            for file in food_model.files:
                src_file = os.path.join(source_dir, file.name)
                if os.path.exists(src_file):
                    shutil.move(src_file, dest_dir)

    def increment_view_count(self, dataset_id: int) -> bool:
        if not isinstance(dataset_id, int) or dataset_id <= 0:
            logger.error(f"ID invalid: {dataset_id}")
            return False
        logger.info(f"Incrementing view count for dataset {dataset_id}")
        return self.repository.increment_view_count(dataset_id)

    def increment_download_count(self, dataset_id: int) -> bool:
        if not isinstance(dataset_id, int) or dataset_id <= 0:
            logger.error(f"ID invalid: {dataset_id}")
            return False
        logger.info(f"Incrementing download count for dataset {dataset_id}")
        return self.repository.increment_download_count(dataset_id)

    def get_trending_datasets(self, period_days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        if period_days not in [7, 30]:
            logger.warning(f"Invalid period: {period_days}, using 7 as default")
            period_days = 7
        limit = min(max(1, limit), 50)
        logger.info(f"Getting trending datasets for period {period_days} days, limit {limit}")
        return self.repository.get_trending_datasets(period_days=period_days, limit=limit)

    def get_trending_weekly(self, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Getting weekly trending datasets, limit {limit}")
        trending_data = self.repository.get_trending_weekly(limit=limit)
        for dataset in trending_data:
            if "recent_downloads_week" not in dataset:
                dataset["recent_downloads_week"] = dataset.get("recent_downloads", 0)
            if "recent_views_week" not in dataset:
                dataset["recent_views_week"] = dataset.get("recent_views", 0)

        return trending_data

    def get_trending_monthly(self, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Getting monthly trending datasets, limit {limit}")
        return self.repository.get_trending_monthly(limit=limit)

    def get_most_viewed_datasets(self, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Getting most viewed datasets, limit {limit}")
        return self.repository.get_most_viewed_datasets(limit=limit)

    def get_most_downloaded_datasets(self, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Getting most downloaded datasets, limit {limit}")
        return self.repository.get_most_downloaded_datasets(limit=limit)

    def get_dataset_stats(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        logger.info(f"Getting stats for dataset {dataset_id}")
        return self.repository.get_dataset_stats(dataset_id)

    def register_dataset_view(self, dataset_id: int) -> bool:
        return self.increment_view_count(dataset_id)

    def register_dataset_download(self, dataset_id: int) -> bool:
        return self.increment_download_count(dataset_id)

    def total_dataset_downloads(self) -> int:
        try:
            total = self.repository.session.query(func.sum(FoodDataset.download_count)).scalar()
            return total or 0
        except Exception as e:
            logger.error(f"Error getting total downloads: {e}")
            return 0

    def total_dataset_views(self) -> int:
        try:
            total = self.repository.session.query(func.sum(FoodDataset.view_count)).scalar()
            return total or 0
        except Exception as e:
            logger.error(f"Error getting total views: {e}")
            return 0

    def total_food_model_downloads(self) -> int:
        try:
            from app.modules.foodmodel.models import FoodModel

            total = self.repository.session.query(func.sum(FoodModel.download_count)).scalar()
            return total or 0
        except Exception as e:
            logger.error(f"Error getting total food model downloads: {e}")
            return 0

    def total_food_model_views(self) -> int:
        try:
            from app.modules.foodmodel.models import FoodModel

            total = self.repository.session.query(func.sum(FoodModel.view_count)).scalar()
            return total or 0
        except Exception as e:
            logger.error(f"Error getting total food model views: {e}")
            return 0

    def count_food_models(self) -> int:
        try:
            from app.modules.foodmodel.models import FoodModel

            total = self.repository.session.query(FoodModel).count()
            return total or 0
        except Exception as e:
            logger.error(f"Error counting food models: {e}")
            return 0

    def get_all_statistics(self) -> Dict[str, Any]:
        return {
            "datasets_counter": self.count_synchronized_datasets(),
            "food_models_counter": self.count_food_models(),
            "total_dataset_downloads": self.total_dataset_downloads(),
            "total_dataset_views": self.total_dataset_views(),
            "total_food_model_downloads": self.total_food_model_downloads(),
            "total_food_model_views": self.total_food_model_views(),
            "trending_weekly": self.get_trending_weekly(limit=3),
            "trending_monthly": self.get_trending_monthly(limit=3),
            "most_viewed": self.get_most_viewed_datasets(limit=5),
            "most_downloaded": self.get_most_downloaded_datasets(limit=5),
            "timestamp": os.getenv("SERVER_TIMESTAMP", "N/A"),
        }
