import logging

from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService
from core.services.SearchService import SearchService

logger = logging.getLogger(__name__)


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())
        self.search_service = SearchService()

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        """
        Intenta buscar en Elastic. Si falla o no hay configuración, usa SQL.
        """
        if self.search_service.enabled:
            try:
                result_ids = self.search_service.search_datasets(query, publication_type, tags)

                if result_ids is not None:
                    logger.info(f"Search used Elasticsearch. Found {len(result_ids)} results.")
                    
                    if len(result_ids) != 0:                    
                        datasets = self.repository.get_by_ids(result_ids)
                        return datasets
                    logger.info("Search used Elasticsearch. Found 0 results. Falling back to SQL.")

            except Exception as e:
                logger.error(f"Unexpected error in Elastic search: {e}. Falling back to SQL.")

        logger.info("Search used SQL fallback.")
        return self.repository.filter(query, sorting, publication_type, tags, **kwargs)
