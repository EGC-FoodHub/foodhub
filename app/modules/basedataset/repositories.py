import logging
from datetime import datetime, timezone
from typing import Optional

from flask_login import current_user
from sqlalchemy import desc, func

from app.modules.basedataset.models import (
    BaseAuthor,
    BaseDataset,
    BaseDOIMapping,
    BaseDSDownloadRecord,
    BaseDSMetaData,
    BaseDSViewRecord,
)
from core.repositories.BaseRepository import BaseRepository

logger = logging.getLogger(__name__)


class BaseAuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseAuthor)


class BaseDSDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDSDownloadRecord)

    def total_dataset_downloads(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class BaseDSMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDSMetaData)

    def filter_by_doi(self, doi: str) -> Optional[BaseDSMetaData]:
        return self.model.query.filter_by(dataset_doi=doi).first()


class BaseDSViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDSViewRecord)

    def total_dataset_views(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0

    def the_record_exists(self, dataset: BaseDataset, user_cookie: str):
        """
        Verifica si existe un registro de vista para cualquier tipo de dataset (BaseDataset).
        """
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_cookie=user_cookie,
        ).first()

    def create_new_record(self, dataset: BaseDataset, user_cookie: str) -> BaseDSViewRecord:
        return self.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_date=datetime.now(timezone.utc),
            view_cookie=user_cookie,
        )


class BaseDOIMappingRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDOIMapping)

    def get_new_doi(self, old_doi: str) -> Optional[str]:
        mapping = self.model.query.filter_by(dataset_doi_old=old_doi).first()
        return mapping.dataset_doi_new if mapping else None


class BaseDatasetRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDataset)

    def get_all_by_user_id(self, user_id: int):
        return self.model.query.filter_by(user_id=user_id).order_by(self.model.created_at.desc()).all()

    def get_latest(self, limit=10):
        return self.model.query.order_by(self.model.created_at.desc()).limit(limit).all()
