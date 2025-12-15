import hashlib
import io
import logging
import os
import shutil
import zipfile
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
from sqlalchemy import func

from app.modules.auth.services import AuthenticationService
from app.modules.basedataset.repositories import BaseAuthorRepository
from app.modules.basedataset.services import BaseDatasetService
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
from app.modules.fooddataset.repositories import FoodDatasetRepository
from app.modules.foodmodel.models import FoodMetaData, FoodModel
from app.modules.foodmodel.repositories import FoodModelRepository
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
        self.author_repository = BaseAuthorRepository()
        self.dsmetadata_repository = self.dsmetadata_repository
        self.food_model_repository = FoodModelRepository()

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
            print(form.dataset_doi.data)
            dsmetadata = FoodDSMetaData(**form.get_dsmetadata())

            self.dsmetadata_repository.session.add(dsmetadata)
            self.dsmetadata_repository.session.flush()

            for author_data in [main_author] + form.get_authors():
                self.author_repository.create(commit=False, food_ds_meta_data_id=dsmetadata.id, **author_data)

            dataset = self.create(commit=False, user_id=current_user.id)

            dataset.ds_meta_data = dsmetadata

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

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

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

    def edit_doi_dataset(self, dataset, form):
        current_user = AuthenticationService().get_authenticated_user()

        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }

        try:
            dsmetadata = dataset.ds_meta_data

            self.author_repository.session.query(self.author_repository.model).filter_by(
                food_ds_meta_data_id=dsmetadata.id
            ).delete()

            new_authors = []
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, food_ds_meta_data_id=dsmetadata.id, **author_data)
                new_authors.append(author)
            dsmetadata.authors = new_authors

            for f in dataset.files:
                self.author_repository.session.query(self.author_repository.model).filter_by(
                    food_meta_data_id=f.food_meta_data.id
                ).delete()
                self.repository.session.delete(f.food_meta_data)
                self.repository.session.delete(f)

            dataset.files.clear()
            self.repository.session.flush()

            new_files = []
            for food_model_form in form.food_models:
                food_metadata = FoodMetaData(**food_model_form.get_food_metadata())
                self.repository.session.add(food_metadata)
                self.repository.session.flush()

                file_authors = []
                for author_data in food_model_form.get_authors():
                    file_author = self.author_repository.create(
                        commit=False, food_meta_data_id=food_metadata.id, **author_data
                    )
                    file_authors.append(file_author)

                file = self.food_model_repository.create(
                    commit=False, data_set_id=dataset.id, food_meta_data_id=food_metadata.id
                )

                new_files.append(file)

            updated_instance = self.update_dsmetadata(dsmetadata.id, **form.get_dsmetadata())

            self.repository.session.commit()

            return updated_instance, None

        except Exception as exc:
            logger.error(f"Exception editing food dataset: {exc}")
            self.repository.session.rollback()
            raise exc

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
            from app.modules.hubfile.models import Hubfile, HubfileDownloadRecord

            total = (
                self.repository.session.query(func.count(HubfileDownloadRecord.id))
                .join(Hubfile, HubfileDownloadRecord.file_id == Hubfile.id)
                .join(FoodModel, Hubfile.food_model_id == FoodModel.id)
                .scalar()
            )
            return total or 0
        except Exception as e:
            logger.error(f"Error getting total food model downloads: {e}")
            return 0

    def total_food_model_views(self) -> int:
        try:
            from app.modules.foodmodel.models import FoodModel
            from app.modules.hubfile.models import Hubfile, HubfileViewRecord

            total = (
                self.repository.session.query(func.count(HubfileViewRecord.id))
                .join(Hubfile, HubfileViewRecord.file_id == Hubfile.id)
                .join(FoodModel, Hubfile.food_model_id == FoodModel.id)
                .scalar()
            )
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

    def create_from_zip(self, form, current_user) -> FoodDataset:
        try:
            dataset = self._create_dataset_shell(form, current_user)

            zip_file = form.zip_file.data
            self._process_zip_file(dataset, zip_file, current_user)

            self.repository.session.commit()

        except Exception as exc:
            logger.exception(f"Exception creating dataset from ZIP...: {exc}")
            self.repository.session.rollback()
            raise exc
        return dataset

    def _process_zip_file(self, dataset, zip_file_obj, current_user):
        temp_folder = current_user.temp_folder()
        os.makedirs(temp_folder, exist_ok=True)

        zip_file_obj.seek(0)
        if not zipfile.is_zipfile(zip_file_obj):
            raise ValueError("File is not a valid ZIP archive.")

        files_count = 0
        with ZipFile(zip_file_obj, "r") as zip_ref:
            for file_path in zip_ref.namelist():
                # accept only .food files inside ZIP
                if (file_path.endswith(".food")) and not file_path.startswith("__MACOSX"):
                    filename = os.path.basename(file_path)
                    if not filename:
                        continue

                    try:
                        file_content = zip_ref.read(file_path)
                        temp_file_path = os.path.join(temp_folder, filename)

                        with open(temp_file_path, "wb") as f:
                            f.write(file_content)

                        fmmetadata = self.fmmetadata_repository.create(commit=False, uvl_filename=filename)
                        fm = self.feature_model_repository.create(
                            commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                        )

                        checksum, size = calculate_checksum_and_size(temp_file_path)
                        hubfile = self.hubfilerepository.create(
                            commit=False, name=filename, checksum=checksum, size=size, feature_model_id=fm.id
                        )
                        fm.files.append(hubfile)

                        files_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to process file '{filename}' from ZIP: {e}")

        if files_count == 0:
            logger.warning(f"No .food files found in the provided ZIP archive for dataset {dataset.id}.")

    def create_from_github(self, form, current_user) -> FoodDataset:
        """
        Procesa la importación de modelos desde un repositorio de GitHub.
        """
        try:
            dataset = self._create_dataset_shell(form, current_user)

            repo_url = form.github_url.data

            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip("/").split("/")

            if parsed_url.hostname != "github.com" or len(path_parts) < 2:
                raise ValueError("Invalid GitHub URL.")

            user_name, repo_name = path_parts[0], path_parts[1]

            api_url = f"https://api.github.com/repos/{user_name}/{repo_name}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            try:
                repo_info = requests.get(api_url, headers=headers)
                repo_info.raise_for_status()
                default_branch = repo_info.json().get("default_branch", "main")
            except requests.RequestException as e:
                logger.warning(f"Could not fetch repo info from GitHub API: {e}. Defaulting to 'main' branch.")
                default_branch = "main"

            zip_url = f"https://github.com/{user_name}/{repo_name}/archive/refs/heads/{default_branch}.zip"
            logger.info(f"Downloading repo from {zip_url}")

            response = requests.get(zip_url, stream=True)
            response.raise_for_status()

            zip_in_memory = io.BytesIO(response.content)

            self._process_zip_file(dataset, zip_in_memory, current_user)

            self.repository.session.commit()

        except requests.RequestException as e:
            logger.exception(f"Exception downloading from GitHub: {e}")
            self.repository.session.rollback()
            raise ValueError("GitHub repository or Branch not found")
        except Exception as exc:
            logger.exception(f"Exception creating dataset from GitHub...: {exc}")
            self.repository.session.rollback()
            raise exc

        return dataset


class SizeService:

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        else:
            return f"{round(size / (1024 ** 3), 2)} GB"
