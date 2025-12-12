from sqlalchemy import func, or_
from app.modules.baseDataset.models import BaseDataset, BaseDSDownloadRecord, BaseDSMetaData, Author
from app import db
from app.modules.recommendations.similarities import SimilarityService
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    
    @staticmethod
    def get_related_BaseDatasets(BaseDataset: BaseDataset, limit: int = 5):
        tags = BaseDataset.ds_meta_data.tags.split(",") if BaseDataset.ds_meta_data.tags else []
        author_ids = [author.id for author in BaseDataset.ds_meta_data.authors] if BaseDataset.ds_meta_data.authors else []

        query = (
            db.session
            .query(BaseDataset)
            .join(BaseDSMetaData)
            .filter(BaseDataset.id != BaseDataset.id)
        )

        has_tags = bool(tags)
        has_authors = bool(author_ids)

        tag_condition = (
            or_(*[
                func.lower(BaseDSMetaData.tags).like(f"%{tag.strip().lower()}%")
                for tag in tags
            ]) if has_tags else None
        )

        author_condition = Author.id.in_(author_ids) if has_authors else None

        if has_tags and has_authors:
            query = (
                query
                .join(BaseDSMetaData.authors)
                .filter(or_(tag_condition, author_condition))
            )
        elif has_tags:
            query = query.filter(tag_condition)
        elif has_authors:
            query = query.join(BaseDSMetaData.authors).filter(author_condition)
        else:
            logger.info("BaseDataset sin tags ni autores para recomendaciones")

        candidates = query.limit(50).all()

        if not candidates:
            return []

        similarity_service = SimilarityService(BaseDataset, candidates)
        ranked = similarity_service.recommendation(n_top_BaseDatasets=limit)

        top_BaseDatasets = [ds for ds, score in ranked]
        for ds, score in ranked:
            print(score)
        return top_BaseDatasets
