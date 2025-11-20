import logging
import os
import uuid
from typing import Optional

from flask import request

from app.modules.basedataset.models import BaseDataset, BaseDSMetaData, BaseDSViewRecord
from app.modules.basedataset.repositories import (
    AuthorRepository,
    BaseDatasetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class BaseDatasetService(BaseService):
    """
    Servicio genérico que proporciona funcionalidad común para
    cualquier tipo de dataset (UVL, Food, etc).
    NO contiene lógica de FeatureModels ni de archivos específicos.
    """

    def __init__(self):
        super().__init__(BaseDatasetRepository())

        # Repositorios comunes
        self.author_repository = AuthorRepository()
        self.metadata_repository = DSMetaDataRepository()
        self.download_repository = DSDownloadRecordRepository()
        self.view_repository = DSViewRecordRepository()
        self.doi_mapping_repository = DOIMappingRepository()

    # -------------------------------------------------------------------------
    # Métodos COMMON: CRUD + queries globales
    # -------------------------------------------------------------------------

    def get_synchronized(self, user_id: int):
        return self.repository.get_synchronized(user_id)

    def get_unsynchronized(self, user_id: int):
        return self.repository.get_unsynchronized(user_id)

    def get_unsynchronized_dataset(self, user_id: int, dataset_id: int):
        return self.repository.get_unsynchronized_dataset(user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_unsynchronized_datasets(self):
        return self.repository.count_unsynchronized_datasets()

    # -------------------------------------------------------------------------
    # Contadores globales
    # -------------------------------------------------------------------------

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_metadata(self) -> int:
        return self.metadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.download_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.view_repository.total_dataset_views()

    # -------------------------------------------------------------------------
    # Creación genérica de datasets
    # NO incluye FeatureModels ni archivos UVL/FOOD
    # -------------------------------------------------------------------------

    def create_from_form(self, form, current_user) -> BaseDataset:
        """
        Crea un dataset genérico.
        Los servicios específicos (UVLDatasetService, FoodDatasetService)
        deben extender este método y añadir la parte específica.
        """
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }

        try:
            # Crear Metadata base
            metadata = self.metadata_repository.create(**form.get_metadata())

            # Autores: principal + adicionales del form
            all_authors = [main_author] + form.get_authors()

            for author_data in all_authors:
                author = self.author_repository.create(commit=False, bd_meta_data_id=metadata.id, **author_data)
                metadata.authors.append(author)

            # Crear el dataset base
            dataset = self.create(commit=False, user_id=current_user.id, bd_meta_data_id=metadata.id)

            # Commit de lo común (el servicio hijo hará commit al final)
            self.repository.session.commit()

        except Exception as exc:
            logger.error(f"Error creating BaseDataset from form: {exc}")
            self.repository.session.rollback()
            raise exc

        return dataset

    # -------------------------------------------------------------------------
    # DOI + URLs
    # -------------------------------------------------------------------------

    def get_dataset_doi_url(self, dataset: BaseDataset) -> str:
        """
        Devuelve una URL estándar para acceder al DOI.
        """
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.bd_meta_data.dataset_doi}"

    # -------------------------------------------------------------------------
    # Vista de datasets: creación de cookies, registro de vistas, etc.
    # -------------------------------------------------------------------------

    def view_record_exists(self, dataset: BaseDataset, user_cookie: str):
        return self.view_repository.the_record_exists(dataset, user_cookie)

    def create_new_view_record(self, dataset: BaseDataset, user_cookie: str) -> BaseDSViewRecord:
        return self.view_repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: BaseDataset) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.view_record_exists(dataset, user_cookie)

        if not existing_record:
            self.create_new_view_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


# -------------------------------------------------------------------------
# Servicios secundarios comunes
# -------------------------------------------------------------------------


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[BaseDSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> Optional[str]:
        mapping = self.repository.get_new_doi(old_doi)
        if mapping:
            return mapping.dataset_doi_new
        return None
