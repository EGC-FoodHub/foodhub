import logging
from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import desc, func, and_

from app.modules.basedataset.repositories import BaseDatasetRepository
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData, FoodDatasetActivity

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

    def increment_view_count(self, dataset_id: int) -> bool:
        try:
            dataset = self.model.query.get(dataset_id)
            if dataset:
                dataset.increment_view()
                self.session.commit()
                logger.info(f"View count incremented for dataset {dataset_id}")
                return True
            logger.warning(f"Dataset {dataset_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error incrementing view count for dataset {dataset_id}: {e}")
            self.session.rollback()
            return False

    def increment_download_count(self, dataset_id: int) -> bool:
        try:
            dataset = self.model.query.get(dataset_id)
            if dataset:
                dataset.increment_download()
                self.session.commit()
                logger.info(f"Download count incremented for dataset {dataset_id}")
                return True
            logger.warning(f"Dataset {dataset_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error incrementing download count for dataset {dataset_id}: {e}")
            self.session.rollback()
            return False

