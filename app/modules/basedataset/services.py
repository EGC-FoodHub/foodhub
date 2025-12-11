import logging
import uuid
import os
from typing import Optional

from flask import request

from app.modules.basedataset.models import BaseDataset, BaseDSMetaData, BaseDSViewRecord
from app.modules.basedataset.repositories import (
    BaseAuthorRepository,
    BaseDatasetRepository,
    BaseDOIMappingRepository,
    BaseDSDownloadRecordRepository,
    BaseDSMetaDataRepository,
    BaseDSViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


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


class BaseDatasetService(BaseService):
    def __init__(self, repository=None):
        super().__init__(repository or BaseDatasetRepository())

        self.author_repository = BaseAuthorRepository()
        self.dsmetadata_repository = BaseDSMetaDataRepository()
        self.dsdownloadrecord_repository = BaseDSDownloadRecordRepository()
        self.dsviewrecord_repository = BaseDSViewRecordRepository()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repository.total_dataset_views()

    def get_by_id(self, id) -> Optional[BaseDataset]:
        return self.repository.get_by_id(id)

    @staticmethod
    def get_doi(dataset: BaseDataset) -> str:
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"


class BaseAuthorService(BaseService):
    def __init__(self):
        super().__init__(BaseAuthorRepository())


class BaseDSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(BaseDSDownloadRecordRepository())


class BaseDSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(BaseDSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[BaseDSMetaData]:
        return self.repository.filter_by_doi(doi)


class BaseDSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(BaseDSViewRecordRepository())

    def the_record_exists(self, dataset: BaseDataset, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: BaseDataset, user_cookie: str) -> BaseDSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: BaseDataset) -> str:
        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class BaseDOIMappingService(BaseService):
    def __init__(self):
        super().__init__(BaseDOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        return doi_mapping.dataset_doi_new if doi_mapping else None
