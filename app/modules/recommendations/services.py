import logging

from sqlalchemy import func, or_

from app import db
from app.modules.basedataset.models import BaseAuthor
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
from app.modules.recommendations.similarities import SimilarityService

logger = logging.getLogger(__name__)


class RecommendationService:

    @staticmethod
    def get_related_food_datasets(dataset: FoodDataset, limit: int = 5):

        ds_meta = dataset.ds_meta_data

        print(f"\n[DEBUG] Base Dataset ID: {dataset.id}")
        print(f"[DEBUG] Base Dataset Title: {ds_meta.title}")
        print(f"[DEBUG] Base Dataset Tags: {ds_meta.tags}")
        print(f"[DEBUG] Base Dataset Authors: {[a.id for a in ds_meta.authors]}")

        tags = ds_meta.tags.split(",") if ds_meta.tags else []
        author_ids = [author.id for author in ds_meta.authors] if ds_meta.authors else []

        query = db.session.query(FoodDataset).filter(FoodDataset.id != dataset.id)

        has_tags = bool(tags)
        has_authors = bool(author_ids)

        tag_condition = (
            or_(*[func.lower(FoodDSMetaData.tags).like(f"%{tag.strip().lower()}%") for tag in tags])
            if has_tags
            else None
        )

        author_names = [author.name.strip() for author in ds_meta.authors] if ds_meta.authors else []

        author_condition = BaseAuthor.name.in_(author_names) if author_names else None

        if has_tags and has_authors:
            query = (
                query.join(FoodDSMetaData, FoodDataset.ds_meta_data)
                .join(FoodDSMetaData.authors)
                .filter(or_(tag_condition, author_condition))
            )
        elif has_tags:
            query = query.join(FoodDSMetaData, FoodDataset.ds_meta_data).filter(tag_condition)
        elif has_authors:
            query = (
                query.join(FoodDSMetaData, FoodDataset.ds_meta_data)
                .join(FoodDSMetaData.authors)
                .filter(author_condition)
            )
        else:
            logger.info("BaseDataset sin tags ni autores para recomendaciones")

        candidates = query.distinct(FoodDataset.id).limit(50).all()

        print(f"[DEBUG] Candidate IDs: {[c.id for c in candidates]}")
        for c in candidates:
            meta = c.ds_meta_data
            print(
                f"[DEBUG] Candidate ID {c.id}, "
                f"Title: {meta.title}, "
                f"Tags: {meta.tags}, "
                f"Authors: {[a.id for a in meta.authors]}"
            )

        if not candidates:
            return []

        similarity_service = SimilarityService(dataset, candidates)
        ranked = similarity_service.recommendation(n_top_datasets=limit)

        top_datasets = [ds for ds, score in ranked]
        for ds, score in ranked:
            print(f"[DEBUG] Ranked Dataset ID {ds.id}, Score: {score}")
        return top_datasets
