from datetime import datetime, timezone
from typing import Optional

from flask_login import current_user
from sqlalchemy import desc, func

from app.modules.basedataset.models import (
    BaseAuthor,
    BaseDataset,
    BaseDSDownloadRecord,
    BaseDSMetaData,
    BaseDSViewRecord,
    BaseDOIMapping,
)
from core.repositories.BaseRepository import BaseRepository

# ----------------------------------------
# Author Repository
# ----------------------------------------


class AuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseAuthor)


# ----------------------------------------
# Download Records
# ----------------------------------------


class DSDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDSDownloadRecord)

    def total_dataset_downloads(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id or 0


# ----------------------------------------
# Metadata
# ----------------------------------------


class DSMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDSMetaData)

    def filter_by_doi(self, doi: str) -> Optional[BaseDSMetaData]:
        return self.model.query.filter_by(dataset_doi=doi).first()


# ----------------------------------------
# View Records
# ----------------------------------------


class DSViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDSViewRecord)

    def total_dataset_views(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id or 0

    def the_record_exists(self, dataset: BaseDataset, user_cookie: str):
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


# ----------------------------------------
# BaseDataset Repository
# ----------------------------------------


class BaseDatasetRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDataset)

    def get_synchronized(self, current_user_id: int):
        return (
            self.model.query.join(BaseDSMetaData)
            .filter(BaseDataset.user_id == current_user_id, BaseDSMetaData.dataset_doi.isnot(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized(self, current_user_id: int):
        return (
            self.model.query.join(BaseDSMetaData)
            .filter(BaseDataset.user_id == current_user_id, BaseDSMetaData.dataset_doi.is_(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int):
        return (
            self.model.query.join(BaseDSMetaData)
            .filter(
                BaseDataset.user_id == current_user_id, BaseDataset.id == dataset_id, BaseDSMetaData.dataset_doi.is_(None)
            )
            .first()
        )

    def count_synchronized_datasets(self):
        return self.model.query.join(BaseDSMetaData).filter(BaseDSMetaData.dataset_doi.isnot(None)).count()

    def count_unsynchronized_datasets(self):
        return self.model.query.join(BaseDSMetaData).filter(BaseDSMetaData.dataset_doi.is_(None)).count()

    def latest_synchronized(self):
        return (
            self.model.query.join(BaseDSMetaData)
            .filter(BaseDSMetaData.dataset_doi.isnot(None))
            .order_by(desc(self.model.id))
            .limit(5)
            .all()
        )


# ----------------------------------------
# DOI Mapping
# ----------------------------------------


class DOIMappingRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDOIMapping)

    def get_new_doi(self, old_doi: str):
        return self.model.query.filter_by(dataset_doi_old=old_doi).first()
