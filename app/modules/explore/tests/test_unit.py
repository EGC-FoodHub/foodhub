from unittest.mock import MagicMock, patch

import pytest

from app.modules.explore.services import ExploreService
from core.services.SearchService import SearchService


# 1. Test para verificar que el indexado llama a Elastic correctamente
def test_index_dataset():
    mock_dataset = MagicMock()
    mock_dataset.id = 1
    mock_dataset.created_at.isoformat.return_value = "2024-01-01"
    mock_dataset.ds_meta_data.title = "Test Dataset"
    mock_dataset.ds_meta_data.description = "Test Description"
    mock_dataset.ds_meta_data.publication_type.name = "ARTICLE"
    mock_dataset.ds_meta_data.tags = "tag1, tag2"

    with patch("core.services.SearchService.Elasticsearch") as MockEs:
        service = SearchService()
        service.es = MagicMock()

        service.index_dataset(mock_dataset)

        service.es.index.assert_called_once()
        call_args = service.es.index.call_args[1]
        assert call_args["index"] == "datasets"
        assert call_args["id"] == 1
        assert call_args["document"]["title"] == "Test Dataset"


# 2. Test para verificar la búsqueda y el parseo de IDs
def test_search_datasets_returns_ids():
    with patch("core.services.SearchService.Elasticsearch") as MockEs:
        service = SearchService()
        service.es = MagicMock()

        mock_response = {"hits": {"hits": [{"_id": "10"}, {"_id": "25"}]}}
        service.es.search.return_value = mock_response

        result_ids = service.search_datasets("query de prueba")

        assert result_ids == [10, 25]
        service.es.search.assert_called_once()


# 3. Test de integración del Servicio Explore: verificar si Elastic devuelve IDs, el servicio Explore filtra por esos IDs
def test_explore_service_uses_search_results():
    with patch("app.modules.explore.services.ExploreRepository") as MockRepositoryClass:
        mock_repo_instance = MockRepositoryClass.return_value

        with patch("app.modules.explore.services.SearchService") as MockSearchService:
            mock_search_instance = MockSearchService.return_value

            mock_search_instance.enabled = True
            mock_search_instance.search_datasets.return_value = [1, 2]

            explore_service = ExploreService()
            explore_service.filter(query="yogur")

            mock_search_instance.search_datasets.assert_called()

            mock_repo_instance.get_by_ids.assert_called_with([1, 2])

            mock_repo_instance.filter.assert_not_called()

 # 4. Test de lógica de negocio (Fallback)
def test_explore_service_falls_back_to_repository_when_search_disabled():
    with patch("app.modules.explore.services.ExploreRepository") as MockRepositoryClass:
        mock_repo_instance = MockRepositoryClass.return_value

        with patch("app.modules.explore.services.SearchService") as MockSearchService:
            mock_search_instance = MockSearchService.return_value
            
            mock_search_instance.enabled = False
            
            explore_service = ExploreService()
            query_text = "test query"
            
            explore_service.filter(query=query_text)

            mock_search_instance.search_datasets.assert_not_called()

            mock_repo_instance.filter.assert_called_once_with(
                query_text, 
                'newest', 
                'any', 
                []
            )
            mock_repo_instance.get_by_ids.assert_not_called()

# 6. Test de Resiliencia: Si Elastic lanza una excepción (caída del servidor, timeout), el servicio debe capturarla y usar SQL transparentemente.
def test_explore_service_handles_elastic_exception_gracefully():
    with patch("app.modules.explore.services.ExploreRepository") as MockRepositoryClass:
        mock_repo_instance = MockRepositoryClass.return_value

        with patch("app.modules.explore.services.SearchService") as MockSearchService:
            mock_search_instance = MockSearchService.return_value
            
            mock_search_instance.enabled = True
            mock_search_instance.search_datasets.side_effect = Exception("Connection Refused to Elastic")
            
            explore_service = ExploreService()
            query_text = "pasta"
            
            explore_service.filter(query=query_text)

            mock_search_instance.search_datasets.assert_called()
            
            mock_repo_instance.filter.assert_called_once_with(
                query_text, 'newest', 'any', [],
            )

# 7. Test de Lógica "Zero Results Fallback": busqueda por SQL si Elasticsearch devuelve lista vacía
def test_explore_service_falls_back_to_sql_when_elastic_returns_empty_list():
    with patch("app.modules.explore.services.ExploreRepository") as MockRepositoryClass:
        mock_repo_instance = MockRepositoryClass.return_value

        with patch("app.modules.explore.services.SearchService") as MockSearchService:
            mock_search_instance = MockSearchService.return_value
            
            mock_search_instance.enabled = True
            mock_search_instance.search_datasets.return_value = []
            
            explore_service = ExploreService()
            query_text = "rare ingredient"
            
            explore_service.filter(query=query_text)

            mock_search_instance.search_datasets.assert_called()

            mock_repo_instance.get_by_ids.assert_not_called()

            mock_repo_instance.filter.assert_called_once_with(
                query_text, 'newest', 'any', [],
            )