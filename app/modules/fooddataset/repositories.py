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

    def get_trending_datasets(self, period_days: int = 7, limit: int = 10) -> List[dict]:
        try:
            cutoff_date = datetime.now() - timedelta(days=period_days)
            
            downloads_subquery = self.session.query(
                FoodDatasetActivity.dataset_id,
                func.count(FoodDatasetActivity.id).label('recent_downloads')
            ).filter(
                and_(
                    FoodDatasetActivity.activity_type == 'download',
                    FoodDatasetActivity.timestamp >= cutoff_date
                )
            ).group_by(FoodDatasetActivity.dataset_id).subquery()
            
            views_subquery = self.session.query(
                FoodDatasetActivity.dataset_id,
                func.count(FoodDatasetActivity.id).label('recent_views')
            ).filter(
                and_(
                    FoodDatasetActivity.activity_type == 'view',
                    FoodDatasetActivity.timestamp >= cutoff_date
                )
            ).group_by(FoodDatasetActivity.dataset_id).subquery()
            
            trending_datasets = self.session.query(
                self.model,
                func.coalesce(downloads_subquery.c.recent_downloads, 0).label('recent_downloads'),
                func.coalesce(views_subquery.c.recent_views, 0).label('recent_views')
            ).outerjoin(
                downloads_subquery, self.model.id == downloads_subquery.c.dataset_id
            ).outerjoin(
                views_subquery, self.model.id == views_subquery.c.dataset_id
            ).order_by(
                (func.coalesce(downloads_subquery.c.recent_downloads, 0) * 2 + 
                 func.coalesce(views_subquery.c.recent_views, 0)).desc()
            ).limit(limit).all()
            

            result = []
            for dataset, recent_downloads, recent_views in trending_datasets:
                trending_dict = dataset.to_trending_dict()
                trending_dict['recent_downloads'] = recent_downloads
                trending_dict['recent_views'] = recent_views
                result.append(trending_dict)
            
            logger.info(f"Retrieved {len(result)} trending datasets for period {period_days} days")
            return result
            
        except Exception as e:
            logger.error(f"Error getting trending datasets: {e}")
            return []

    def get_trending_weekly(self, limit: int = 10) -> List[dict]:
        return self.get_trending_datasets(period_days=7, limit=limit)

    def get_trending_monthly(self, limit: int = 10) -> List[dict]:
        return self.get_trending_datasets(period_days=30, limit=limit)

    def get_most_viewed_datasets(self, limit: int = 10) -> List[dict]:
        try:
            datasets = (
                self.model.query
                .filter(self.model.view_count > 0)
                .order_by(desc(self.model.view_count))
                .limit(limit)
                .all()
            )
            
            return [dataset.to_trending_dict() for dataset in datasets]
        except Exception as e:
            logger.error(f"Error getting most viewed datasets: {e}")
            return []

    def get_most_downloaded_datasets(self, limit: int = 10) -> List[dict]:
        try:
            datasets = (
                self.model.query
                .filter(self.model.download_count > 0)
                .order_by(desc(self.model.download_count))
                .limit(limit)
                .all()
            )
            
            return [dataset.to_trending_dict() for dataset in datasets]
        except Exception as e:
            logger.error(f"Error getting most downloaded datasets: {e}")
            return []

    def get_dataset_stats(self, dataset_id: int) -> Optional[dict]:
        try:
            dataset = self.model.query.get(dataset_id)
            if dataset:
                return dataset.to_trending_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting dataset stats for {dataset_id}: {e}")
            return None