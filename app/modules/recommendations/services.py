from sqlalchemy import func, or_
from app.modules.dataset.models import DataSet, DSDownloadRecord, DSMetaData, Author
from app import db
from app.modules.recommendations.similarities import SimilarityService
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    
    @staticmethod
    def get_related_datasets(dataset: DataSet, limit: int = 5):
        tags = dataset.ds_meta_data.tags.split(",") if dataset.ds_meta_data.tags else []
        author_ids = [author.id for author in dataset.ds_meta_data.authors] if dataset.ds_meta_data.authors else []

        query = (
            db.session
            .query(DataSet)
            .join(DSMetaData)
            .filter(DataSet.id != dataset.id)
        )

        has_tags = bool(tags)
        has_authors = bool(author_ids)

        tag_condition = (
            or_(*[
                func.lower(DSMetaData.tags).like(f"%{tag.strip().lower()}%")
                for tag in tags
            ]) if has_tags else None
        )

        author_condition = Author.id.in_(author_ids) if has_authors else None

        if has_tags and has_authors:
            query = (
                query
                .join(DSMetaData.authors)
                .filter(or_(tag_condition, author_condition))
            )
        elif has_tags:
            query = query.filter(tag_condition)
        elif has_authors:
            query = query.join(DSMetaData.authors).filter(author_condition)
        else:
            logger.info("Dataset sin tags ni autores para recomendaciones")

        candidates = query.limit(50).all()

        if not candidates:
            return []

        similarity_service = SimilarityService(dataset, candidates)
        ranked = similarity_service.recommendation(n_top_datasets=limit)

        top_datasets = [ds for ds, score in ranked]
        for ds, score in ranked:
            print(score)
        return top_datasets
