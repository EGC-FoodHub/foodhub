import logging
from typing import Optional

from sqlalchemy import desc

from app.modules.basedataset.repositories import BaseDatasetRepository
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData

logger = logging.getLogger(__name__)


class FoodDatasetRepository(BaseDatasetRepository):
    def __init__(self):
        super().__init__()
        self.model = FoodDataset

    def get_synchronized(self, current_user_id: int):
        return (
            self.model.query.join(FoodDSMetaData)
            .filter(FoodDataset.user_id == current_user_id, FoodDSMetaData.dataset_doi.isnot(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized(self, current_user_id: int):
        return (
            self.model.query.join(FoodDSMetaData)
            .filter(FoodDataset.user_id == current_user_id, FoodDSMetaData.dataset_doi.is_(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> Optional[FoodDataset]:
        return (
            self.model.query.join(FoodDSMetaData)
            .filter(
                FoodDataset.user_id == current_user_id,
                FoodDataset.id == dataset_id,
                FoodDSMetaData.dataset_doi.is_(None),
            )
            .first()
        )

    def count_synchronized_datasets(self):
        return self.model.query.join(FoodDSMetaData).filter(FoodDSMetaData.dataset_doi.isnot(None)).count()

    def count_unsynchronized_datasets(self):
        return self.model.query.join(FoodDSMetaData).filter(FoodDSMetaData.dataset_doi.is_(None)).count()

    def latest_synchronized(self):
        return (
            self.model.query.join(FoodDSMetaData)
            .filter(FoodDSMetaData.dataset_doi.isnot(None))
            .order_by(desc(self.model.id))
            .limit(5)
            .all()
        )
