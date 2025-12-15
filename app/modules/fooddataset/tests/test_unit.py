from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func
from app import db
from app.modules.auth.models import User
from app.modules.basedataset.models import BaseAuthor, BasePublicationType
from app.modules.fooddataset.models import (
    FoodDataset,
    FoodDatasetActivity,
    FoodDSMetaData,
    FoodNutritionalValue,
)


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Create a user for testing
        user = User.query.filter_by(email="test_food@example.com").first()
        if not user:
            user = User(email="test_food@example.com", is_email_verified=True)
            user.set_password("test1234")
            db.session.add(user)
            db.session.commit()

        # Create a sample FoodDataset
        ds_meta = FoodDSMetaData(
            title="Food Dataset 1",
            description="Delicious food data",
            publication_type=BasePublicationType.JOURNAL_ARTICLE,
            calories="500",
            type="Recipe",
            community="Foodies",
        )

        # Add an author
        author = BaseAuthor(name="Chef Test", affiliation="Kitchen", orcid="0000-0000-0000-0000")
        ds_meta.authors.append(author)

        # Add nutritional value
        nutri = FoodNutritionalValue(name="Protein", value="20g")
        ds_meta.nutritional_values.append(nutri)

        dataset = FoodDataset(user_id=user.id, ds_meta_data=ds_meta)
        db.session.add(dataset)
        db.session.commit()

    yield test_client

    # Cleanup is handled by the rollback in the outer fixture usually,
    # but if scope is module, we might want explicit cleanup if needed.
    # For now, relying on default behavior.


def test_food_dataset_creation(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()
        assert dataset is not None
        assert dataset.ds_meta_data.title == "Food Dataset 1"
        assert dataset.ds_meta_data.calories == "500"
        assert len(dataset.ds_meta_data.authors) == 1
        assert dataset.ds_meta_data.authors[0].name == "Chef Test"


def test_increment_view(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()
        initial_views = dataset.view_count

        dataset.increment_view()
        db.session.commit()

        assert dataset.view_count == initial_views + 1
        assert dataset.last_viewed_at is not None

        # Check activity log
        log = (
            FoodDatasetActivity.query.filter_by(dataset_id=dataset.id, activity_type="view")
            .order_by(FoodDatasetActivity.timestamp.desc())
            .first()
        )
        assert log is not None


def test_increment_download(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()
        initial_downloads = dataset.download_count

        dataset.increment_download()
        db.session.commit()

        assert dataset.download_count == initial_downloads + 1
        assert dataset.last_downloaded_at is not None

        # Check activity log
        log = (
            FoodDatasetActivity.query.filter_by(dataset_id=dataset.id, activity_type="download")
            .order_by(FoodDatasetActivity.timestamp.desc())
            .first()
        )
        assert log is not None


def test_get_recent_views_and_downloads(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()

        # We just added 1 view and 1 download in previous tests
        assert dataset.get_recent_views(days=1) >= 1
        assert dataset.get_recent_downloads(days=1) >= 1

        # Test with 0 days (should still include today's activity)
        assert dataset.get_recent_views(days=7) >= 1


def test_calculate_trending_score(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()

        # We assume at least 1 view and 1 download exist from previous tests
        downloads = dataset.get_recent_downloads(7)
        views = dataset.get_recent_views(7)

        expected_score = (downloads * 2.0) + (views * 1.0)
        assert dataset.calculate_trending_score(days=7, download_weight=2.0, view_weight=1.0) == expected_score


def test_get_main_author(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()
        author_info = dataset.get_main_author()

        assert author_info is not None
        assert author_info["name"] == "Chef Test"
        assert author_info["affiliation"] == "Kitchen"


def test_get_main_author_none(test_client):
    # Create a dataset without authors
    with test_client.application.app_context():
        ds_meta = FoodDSMetaData(title="No Author DS", description="desc", publication_type=BasePublicationType.OTHER)
        user = User.query.first()
        ds = FoodDataset(user_id=user.id, ds_meta_data=ds_meta)
        db.session.add(ds)
        db.session.commit()

        assert ds.get_main_author() is None

        # Clean up
        db.session.delete(ds)
        db.session.commit()


def test_to_trending_dict(test_client):
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()
        data = dataset.to_trending_dict()

        assert data["title"] == "Food Dataset 1"
        assert data["community"] == "Foodies"
        assert data["view_count"] >= 1
        assert "trending_score" in data
        assert "main_author" in data


def test_get_trending(test_client):
    with test_client.application.app_context():
        trending = FoodDataset.get_trending(limit=5)
        assert len(trending) > 0

        # Verify order (descending by score)
        if len(trending) > 1:
            for i in range(len(trending) - 1):
                assert trending[i]["trending_score"] >= trending[i + 1]["trending_score"]


def test_activity_log_creation(test_client):
    # Verify that activity logs are correctly linked
    with test_client.application.app_context():
        dataset = FoodDataset.query.join(FoodDSMetaData).filter(FoodDSMetaData.title == "Food Dataset 1").first()
        logs = dataset.activity_logs
        assert len(logs) > 0
        assert logs[0].dataset_id == dataset.id


def test_service_get_doi(test_client):
    from app.modules.fooddataset.services import FoodDatasetService

    service = FoodDatasetService()

    dataset = MagicMock()
    dataset.ds_meta_data.dataset_doi = "10.1234/test"

    # helper to mock env if needed, but default is localhost
    doi_url = service.get_doi(dataset)
    # The URL might include port 5000 in test environment
    assert "http://" in doi_url
    assert "/doi/10.1234/test" in doi_url


def test_service_create_from_form(test_client):
    from app.modules.fooddataset.services import FoodDatasetService

    # Mocking behaviors
    with (
        patch("app.modules.fooddataset.services.FoodDatasetRepository"),
        patch("app.modules.fooddataset.services.HubfileRepository"),
        patch("app.modules.fooddataset.services.calculate_checksum_and_size") as mock_checksum,
    ):

        service = FoodDatasetService()
        # Manually mock inherited repositories that are created in __init__
        service.dsmetadata_repository = MagicMock()
        service.author_repository = MagicMock()

        # Setup Mocks
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.profile.surname = "Doe"
        mock_user.profile.name = "John"
        mock_user.temp_folder.return_value = "/tmp/test"

        mock_form = MagicMock()
        mock_form.get_dsmetadata.return_value = {
            "title": "Test DS",
            "description": "Desc",
            "publication_type": BasePublicationType.NONE,
            "calories": "100",
            "type": "T",
            "community": "C",
        }
        mock_form.get_authors.return_value = []

        # Mock food model form
        mock_food_form = MagicMock()
        mock_food_form.filename.data = "test.food"
        # Correct fields for FoodMetaData
        mock_food_form.get_food_metadata.return_value = {"food_filename": "f1", "title": "t1", "description": "d1"}
        mock_food_form.get_authors.return_value = []
        mock_form.food_models = [mock_food_form]

        mock_checksum.return_value = ("hash", 100)

        # Mock the internal move method to avoid complex setup of dataset.files on the mock
        service._move_dataset_files = MagicMock()

        # Run create
        ds = service.create_from_form(mock_form, mock_user)

        # Verify interactions
        assert ds is not None
        service.dsmetadata_repository.session.add.assert_called()
        service.repository.session.commit.assert_called()
        service._move_dataset_files.assert_called()


def test_service_move_dataset_files(test_client):
    from app.modules.fooddataset.services import FoodDatasetService

    with (
        patch("app.modules.fooddataset.services.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.services.os.makedirs") as mock_makedirs,
        patch("app.modules.fooddataset.services.shutil.move") as mock_move,
    ):

        service = FoodDatasetService()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.temp_folder.return_value = "/tmp"

        dataset = MagicMock()
        dataset.id = 123

        # Setup specific file structure
        f_model = MagicMock()
        hubfile = MagicMock()
        hubfile.name = "test.food"
        f_model.files = [hubfile]
        dataset.files = [f_model]

        mock_exists.return_value = True

        service._move_dataset_files(dataset, mock_user)

        mock_move.assert_called()
        mock_makedirs.assert_called()


def test_service_passthrough_methods(test_client):
    from app.modules.fooddataset.services import FoodDatasetService

    with patch("app.modules.fooddataset.services.FoodDatasetRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()

        # Test get_synchronized
        service.get_synchronized(1)
        mock_repo_instance.get_synchronized.assert_called_with(1)

        # Test get_unsynchronized
        service.get_unsynchronized(1)
        mock_repo_instance.get_unsynchronized.assert_called_with(1)

        # Test get_unsynchronized_dataset
        service.get_unsynchronized_dataset(1, 2)
        mock_repo_instance.get_unsynchronized_dataset.assert_called_with(1, 2)

        # Test latest_synchronized
        service.latest_synchronized()
        mock_repo_instance.latest_synchronized.assert_called()

        # Test count_synchronized_datasets
        service.count_synchronized_datasets()
        mock_repo_instance.count_synchronized_datasets.assert_called()

        # Test count_unsynchronized_datasets
        service.count_unsynchronized_datasets()
        mock_repo_instance.count_unsynchronized_datasets.assert_called()


def test_route_dataset_upload_get(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    response = test_client.get("/dataset/upload")
    assert response.status_code == 200
    assert b"Upload</b> Food Dataset" in response.data


def test_route_dataset_upload_post_success(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service_instance,
        patch("app.modules.fooddataset.routes.ZenodoService") as MockZenodo,
        patch("app.modules.fooddataset.routes.shutil.rmtree") as mock_rmtree,
        patch("app.modules.fooddataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("app.modules.auth.models.User.temp_folder") as mock_temp_folder,
    ):

        mock_dataset = MagicMock()
        mock_dataset.id = 1
        mock_dataset.files = []
        mock_service_instance.create_from_form.return_value = mock_dataset

        mock_zenodo_instance = MockZenodo.return_value
        mock_zenodo_instance.create_new_deposition.return_value = {"id": 123, "conceptrecid": 456}

        mock_exists.return_value = True
        mock_temp_folder.return_value = "/tmp"

        mock_form_instance = MockForm.return_value
        mock_form_instance.validate_on_submit.return_value = True

        # Simulate POST request
        response = test_client.post("/dataset/upload", data={"title": "Test Title"})

        # Print error if failure
        if response.status_code != 200:
            print(f"Response: {response.data}")

        assert response.status_code == 200
        assert response.json["message"] == "Dataset created successfully!"
        mock_rmtree.assert_called()


def test_route_file_upload(test_client):
    from io import BytesIO

    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    with (
        patch("app.modules.auth.models.User.temp_folder") as mock_temp_folder,
        patch("app.modules.fooddataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.routes.os.makedirs") as mock_makedirs,
    ):

        mock_temp_folder.return_value = "/tmp"
        mock_exists.return_value = False

        data = {"file": (BytesIO(b"content"), "test.food")}

        with patch("werkzeug.datastructures.FileStorage.save") as mock_save:
            response = test_client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")
            assert response.status_code == 200
            assert response.json["message"] == "File uploaded successfully"
            mock_makedirs.assert_called()
            mock_save.assert_called()


def test_route_file_delete(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    with (
        patch("app.modules.auth.models.User.temp_folder") as mock_temp_folder,
        patch("app.modules.fooddataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.routes.os.remove") as mock_remove,
    ):

        mock_temp_folder.return_value = "/tmp"
        mock_exists.return_value = True

        response = test_client.post("/dataset/file/delete", json={"file": "test.food"})
        assert response.status_code == 200
        assert response.json["message"] == "File deleted successfully"
        mock_remove.assert_called()


def test_route_dataset_upload_bad_request(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    # Test with empty data to trigger validation error
    response = test_client.post("/dataset/upload", data={})
    assert response.status_code == 400
    # The form errors are returned in the message
    assert b"message" in response.data


def test_route_dataset_upload_zenodo_failure(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service_instance,
        patch("app.modules.fooddataset.routes.ZenodoService") as MockZenodo,
        patch("app.modules.fooddataset.routes.shutil.rmtree") as mock_rmtree,
        patch("app.modules.fooddataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("app.modules.auth.models.User.temp_folder") as mock_temp_folder,
    ):

        # Successful dataset creation
        mock_dataset = MagicMock()
        mock_dataset.id = 1
        mock_dataset.files = []
        mock_service_instance.create_from_form.return_value = mock_dataset

        # Zenodo failure
        mock_zenodo_instance = MockZenodo.return_value
        mock_zenodo_instance.create_new_deposition.side_effect = Exception("Zenodo Down")

        mock_exists.return_value = True
        mock_temp_folder.return_value = "/tmp"

        mock_form_instance = MockForm.return_value
        mock_form_instance.validate_on_submit.return_value = True

        # Should still return 200 but maybe with a warning or just success message
        # (Current implementation swallows Zenodo errors and returns success)
        response = test_client.post("/dataset/upload", data={"title": "Test Title"})

        assert response.status_code == 200
        assert response.json["message"] == "Dataset created successfully!"
        # Verify Zenodo was attempted
        mock_zenodo_instance.create_new_deposition.assert_called()
        mock_rmtree.assert_called()


def test_route_dataset_upload_general_exception(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service_instance,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
    ):

        mock_form_instance = MockForm.return_value
        mock_form_instance.validate_on_submit.return_value = True

        # Service raises exception
        mock_service_instance.create_from_form.side_effect = Exception("General Error")

        response = test_client.post("/dataset/upload", data={"title": "Test Title"})

        assert response.status_code == 400
        assert b"General Error" in response.data

#test trending

def test_increment_view_count_valid(test_client):
    """Test increment_view_count con ID válido"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        # Configurar el mock para devolver True
        mock_repo_instance.increment_view_count.return_value = True
        
        # Caso válido
        result = service.increment_view_count(123)
        
        assert result is True
        mock_repo_instance.increment_view_count.assert_called_once_with(123)


def test_increment_view_count_invalid(test_client):
    """Test increment_view_count con IDs inválidos"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        # ID no entero
        result = service.increment_view_count("invalid")
        assert result is False
        
        # ID negativo
        result = service.increment_view_count(-1)
        assert result is False
        
        # ID cero
        result = service.increment_view_count(0)
        assert result is False
        
        # El repositorio no debería haber sido llamado
        mock_repo_instance.increment_view_count.assert_not_called()


def test_increment_download_count_valid(test_client):
    """Test increment_download_count con ID válido"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        mock_repo_instance.increment_download_count.return_value = True
        
        result = service.increment_download_count(456)
        
        assert result is True
        mock_repo_instance.increment_download_count.assert_called_once_with(456)


def test_increment_download_count_invalid(test_client):
    """Test increment_download_count con IDs inválidos"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        # Varios casos inválidos
        test_cases = ["invalid", -5, 0]
        for test_id in test_cases:
            result = service.increment_download_count(test_id)
            assert result is False
        
        # El repositorio no debería haber sido llamado
        mock_repo_instance.increment_download_count.assert_not_called()


def test_get_trending_datasets_valid_period(test_client):
    """Test get_trending_datasets con períodos válidos"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        mock_data = [
            {"id": 1, "title": "Dataset 1", "trending_score": 15.5},
            {"id": 2, "title": "Dataset 2", "trending_score": 12.0}
        ]
        mock_repo_instance.get_trending_datasets.return_value = mock_data
        
        # Test con período 7 días
        result = service.get_trending_datasets(period_days=7, limit=10)
        assert result == mock_data
        mock_repo_instance.get_trending_datasets.assert_called_with(period_days=7, limit=10)
        
        # Reset mock
        mock_repo_instance.reset_mock()
        mock_repo_instance.get_trending_datasets.return_value = mock_data
        
        # Test con período 30 días
        result = service.get_trending_datasets(period_days=30, limit=5)
        assert result == mock_data
        mock_repo_instance.get_trending_datasets.assert_called_with(period_days=30, limit=5)


def test_get_trending_datasets_invalid_period(test_client):
    """Test get_trending_datasets con período inválido"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        mock_data = [{"id": 1, "title": "Test Dataset"}]
        mock_repo_instance.get_trending_datasets.return_value = mock_data
        
        # Período inválido debería usar 7 por defecto
        result = service.get_trending_datasets(period_days=15, limit=10)
        assert result == mock_data
        mock_repo_instance.get_trending_datasets.assert_called_with(period_days=7, limit=10)


def test_get_trending_datasets_limit_boundaries(test_client):
    """Test get_trending_datasets con límites en los bordes"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        # Test límite mínimo (debería ser 1)
        service.get_trending_datasets(period_days=7, limit=0)
        mock_repo_instance.get_trending_datasets.assert_called_with(period_days=7, limit=1)
        
        # Reset mock
        mock_repo_instance.reset_mock()
        
        # Test límite máximo (debería ser 50)
        service.get_trending_datasets(period_days=7, limit=100)
        mock_repo_instance.get_trending_datasets.assert_called_with(period_days=7, limit=50)
        
        # Reset mock
        mock_repo_instance.reset_mock()
        
        # Test límite normal
        service.get_trending_datasets(period_days=7, limit=25)
        mock_repo_instance.get_trending_datasets.assert_called_with(period_days=7, limit=25)


def test_get_trending_weekly(test_client):
    """Test get_trending_weekly"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        # Datos del repositorio sin campos week
        repo_data = [
            {"id": 1, "title": "Dataset 1", "recent_downloads": 5, "recent_views": 10},
            {"id": 2, "title": "Dataset 2", "recent_downloads": 3}
        ]
        mock_repo_instance.get_trending_weekly.return_value = repo_data
        
        result = service.get_trending_weekly(limit=10)
        
        # Verificar que se añaden los campos week
        assert len(result) == 2
        assert result[0]["recent_downloads_week"] == 5
        assert result[0]["recent_views_week"] == 10
        assert result[1]["recent_downloads_week"] == 3
        assert result[1]["recent_views_week"] == 0  # Valor por defecto
        
        mock_repo_instance.get_trending_weekly.assert_called_once_with(limit=10)


def test_get_trending_monthly(test_client):
    """Test get_trending_monthly"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        mock_data = [{"id": 1, "title": "Monthly Trending"}]
        mock_repo_instance.get_trending_monthly.return_value = mock_data
        
        result = service.get_trending_monthly(limit=5)
        
        assert result == mock_data
        mock_repo_instance.get_trending_monthly.assert_called_once_with(limit=5)


def test_get_most_viewed_datasets(test_client):
    """Test get_most_viewed_datasets"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        mock_data = [
            {"id": 1, "title": "Most Viewed 1", "view_count": 100},
            {"id": 2, "title": "Most Viewed 2", "view_count": 80}
        ]
        mock_repo_instance.get_most_viewed_datasets.return_value = mock_data
        
        result = service.get_most_viewed_datasets(limit=3)
        
        assert result == mock_data
        mock_repo_instance.get_most_viewed_datasets.assert_called_once_with(limit=3)


def test_get_most_downloaded_datasets(test_client):
    """Test get_most_downloaded_datasets"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        mock_data = [
            {"id": 1, "title": "Most Downloaded 1", "download_count": 50},
            {"id": 2, "title": "Most Downloaded 2", "download_count": 30}
        ]
        mock_repo_instance.get_most_downloaded_datasets.return_value = mock_data
        
        result = service.get_most_downloaded_datasets(limit=4)
        
        assert result == mock_data
        mock_repo_instance.get_most_downloaded_datasets.assert_called_once_with(limit=4)


def test_get_dataset_stats(test_client):
    """Test get_dataset_stats"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        service = FoodDatasetService()
        
        # Caso con datos
        mock_stats = {
            "id": 123,
            "title": "Test Dataset",
            "view_count": 45,
            "download_count": 12,
            "created_at": "2023-01-01"
        }
        mock_repo_instance.get_dataset_stats.return_value = mock_stats
        
        result = service.get_dataset_stats(123)
        assert result == mock_stats
        mock_repo_instance.get_dataset_stats.assert_called_once_with(123)
        
        # Reset mock
        mock_repo_instance.reset_mock()
        
        # Caso sin datos
        mock_repo_instance.get_dataset_stats.return_value = None
        result = service.get_dataset_stats(999)
        assert result is None
        mock_repo_instance.get_dataset_stats.assert_called_once_with(999)


def test_register_dataset_view(test_client):
    """Test register_dataset_view (alias de increment_view_count)"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    service = FoodDatasetService()
    
    with patch.object(service, 'increment_view_count', return_value=True) as mock_increment:
        result = service.register_dataset_view(123)
        
        assert result is True
        mock_increment.assert_called_once_with(123)


def test_register_dataset_download(test_client):
    """Test register_dataset_download (alias de increment_download_count)"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    service = FoodDatasetService()
    
    with patch.object(service, 'increment_download_count', return_value=True) as mock_increment:
        result = service.register_dataset_download(456)
        
        assert result is True
        mock_increment.assert_called_once_with(456)


def test_total_dataset_downloads(test_client):
    """Test total_dataset_downloads"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.fooddataset.models import FoodDataset
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        # Configurar el mock de la sesión y query
        mock_query = MagicMock()
        mock_scalar = MagicMock()
        
        mock_repo_instance.session.query.return_value = mock_query
        mock_query.scalar.return_value = 150
        
        service = FoodDatasetService()
        
        result = service.total_dataset_downloads()
        
        assert result == 150
        mock_repo_instance.session.query.assert_called_once_with(func.sum(FoodDataset.download_count))


def test_total_dataset_downloads_error(test_client):
    """Test total_dataset_downloads con error"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.fooddataset.models import FoodDataset
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        # Simular error en la query
        mock_repo_instance.session.query.side_effect = Exception("Database error")
        
        service = FoodDatasetService()
        
        result = service.total_dataset_downloads()
        
        assert result == 0


def test_total_dataset_downloads_none_result(test_client):
    """Test total_dataset_downloads cuando scalar devuelve None"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.fooddataset.models import FoodDataset
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        mock_query = MagicMock()
        mock_repo_instance.session.query.return_value = mock_query
        mock_query.scalar.return_value = None
        
        service = FoodDatasetService()
        
        result = service.total_dataset_downloads()
        
        assert result == 0


def test_total_dataset_views(test_client):
    """Test total_dataset_views"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.fooddataset.models import FoodDataset
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        mock_query = MagicMock()
        mock_repo_instance.session.query.return_value = mock_query
        mock_query.scalar.return_value = 300
        
        service = FoodDatasetService()
        
        result = service.total_dataset_views()
        
        assert result == 300
        mock_repo_instance.session.query.assert_called_once_with(func.sum(FoodDataset.view_count))


def test_total_food_model_downloads(test_client):
    """Test total_food_model_downloads"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.foodmodel.models import FoodModel
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        mock_query = MagicMock()
        mock_repo_instance.session.query.return_value = mock_query
        mock_query.scalar.return_value = 75
        
        service = FoodDatasetService()
        
        result = service.total_food_model_downloads()
        
        assert result == 75
        # Verificar que se importó FoodModel correctamente
        mock_repo_instance.session.query.assert_called_once_with(func.sum(FoodModel.download_count))


def test_total_food_model_downloads_import_error(test_client):
    """Test total_food_model_downloads con error de importación"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        # Simular error al importar FoodModel
        with patch('app.modules.fooddataset.services.FoodModel', side_effect=ImportError("Module not found")):
            service = FoodDatasetService()
            result = service.total_food_model_downloads()
            
            assert result == 0


def test_total_food_model_views(test_client):
    """Test total_food_model_views"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.foodmodel.models import FoodModel
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        mock_query = MagicMock()
        mock_repo_instance.session.query.return_value = mock_query
        mock_query.scalar.return_value = 120
        
        service = FoodDatasetService()
        
        result = service.total_food_model_views()
        
        assert result == 120
        mock_repo_instance.session.query.assert_called_once_with(func.sum(FoodModel.view_count))


def test_count_food_models(test_client):
    """Test count_food_models"""
    from app.modules.fooddataset.services import FoodDatasetService
    from app.modules.foodmodel.models import FoodModel
    
    with patch('app.modules.fooddataset.services.FoodDatasetRepository') as MockRepo:
        mock_repo_instance = MockRepo.return_value
        
        mock_query = MagicMock()
        mock_repo_instance.session.query.return_value = mock_query
        mock_query.count.return_value = 25
        
        service = FoodDatasetService()
        
        result = service.count_food_models()
        
        assert result == 25
        mock_repo_instance.session.query.assert_called_once_with(FoodModel)


def test_get_all_statistics(test_client):
    """Test get_all_statistics completo"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    service = FoodDatasetService()
    
    with patch.object(service, 'count_synchronized_datasets', return_value=10) as mock_count_synced, \
         patch.object(service, 'count_food_models', return_value=25) as mock_count_food, \
         patch.object(service, 'total_dataset_downloads', return_value=150) as mock_total_ds_dl, \
         patch.object(service, 'total_dataset_views', return_value=300) as mock_total_ds_views, \
         patch.object(service, 'total_food_model_downloads', return_value=75) as mock_total_food_dl, \
         patch.object(service, 'total_food_model_views', return_value=120) as mock_total_food_views, \
         patch.object(service, 'get_trending_weekly', return_value=[
             {"id": 1, "title": "Weekly 1"},
             {"id": 2, "title": "Weekly 2"},
             {"id": 3, "title": "Weekly 3"}
         ]) as mock_trending_weekly, \
         patch.object(service, 'get_trending_monthly', return_value=[
             {"id": 4, "title": "Monthly 1"},
             {"id": 5, "title": "Monthly 2"},
             {"id": 6, "title": "Monthly 3"}
         ]) as mock_trending_monthly, \
         patch.object(service, 'get_most_viewed_datasets', return_value=[
             {"id": 7, "title": "Most Viewed 1"},
             {"id": 8, "title": "Most Viewed 2"}
         ]) as mock_most_viewed, \
         patch.object(service, 'get_most_downloaded_datasets', return_value=[
             {"id": 9, "title": "Most Downloaded 1"},
             {"id": 10, "title": "Most Downloaded 2"}
         ]) as mock_most_downloaded, \
         patch('app.modules.fooddataset.services.os.getenv', return_value="2023-12-15 10:30:00") as mock_getenv:
        
        result = service.get_all_statistics()
        
        # Verificar estructura del resultado
        assert isinstance(result, dict)
        assert result["datasets_counter"] == 10
        assert result["food_models_counter"] == 25
        assert result["total_dataset_downloads"] == 150
        assert result["total_dataset_views"] == 300
        assert result["total_food_model_downloads"] == 75
        assert result["total_food_model_views"] == 120
        assert len(result["trending_weekly"]) == 3
        assert len(result["trending_monthly"]) == 3
        assert len(result["most_viewed"]) == 2
        assert len(result["most_downloaded"]) == 2
        assert result["timestamp"] == "2023-12-15 10:30:00"
        
        # Verificar que se llamaron los métodos con los parámetros correctos
        mock_count_synced.assert_called_once()
        mock_count_food.assert_called_once()
        mock_total_ds_dl.assert_called_once()
        mock_total_ds_views.assert_called_once()
        mock_total_food_dl.assert_called_once()
        mock_total_food_views.assert_called_once()
        mock_trending_weekly.assert_called_once_with(limit=3)
        mock_trending_monthly.assert_called_once_with(limit=3)
        mock_most_viewed.assert_called_once_with(limit=5)
        mock_most_downloaded.assert_called_once_with(limit=5)
        mock_getenv.assert_called_once_with("SERVER_TIMESTAMP", "N/A")


def test_get_all_statistics_env_var_missing(test_client):
    """Test get_all_statistics cuando falta la variable de entorno"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    service = FoodDatasetService()
    
    with patch.object(service, 'count_synchronized_datasets', return_value=5), \
         patch.object(service, 'count_food_models', return_value=10), \
         patch.object(service, 'total_dataset_downloads', return_value=100), \
         patch.object(service, 'total_dataset_views', return_value=200), \
         patch.object(service, 'total_food_model_downloads', return_value=50), \
         patch.object(service, 'total_food_model_views', return_value=80), \
         patch.object(service, 'get_trending_weekly', return_value=[]), \
         patch.object(service, 'get_trending_monthly', return_value=[]), \
         patch.object(service, 'get_most_viewed_datasets', return_value=[]), \
         patch.object(service, 'get_most_downloaded_datasets', return_value=[]), \
         patch('app.modules.fooddataset.services.os.getenv', return_value=None) as mock_getenv:
        
        result = service.get_all_statistics()
        
        assert result["timestamp"] == "N/A"
        mock_getenv.assert_called_once_with("SERVER_TIMESTAMP", "N/A")


def test_get_all_statistics_with_real_data(test_client):
    """Test get_all_statistics integrado con datos reales"""
    from app.modules.fooddataset.services import FoodDatasetService
    
    with test_client.application.app_context():
        # Crear datos de prueba en la base de datos
        from app import db
        from app.modules.auth.models import User
        from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
        from app.modules.foodmodel.models import FoodModel
        
        # Crear usuario
        user = User(email="stats_test@example.com", is_email_verified=True)
        user.set_password("test1234")
        db.session.add(user)
        db.session.flush()  # Para obtener el ID
        
        # Crear datasets
        for i in range(3):
            ds_meta = FoodDSMetaData(
                title=f"Stats Dataset {i}",
                description="Test for statistics",
                publication_type="Journal Article",
                calories="500",
                type="Recipe",
                community="Testers"
            )
            dataset = FoodDataset(
                user_id=user.id,
                ds_meta_data=ds_meta,
                view_count=i * 10,
                download_count=i * 5
            )
            db.session.add(dataset)
        
        # Crear food models (simulado, ya que FoodModel puede no existir en el módulo)
        # Esto es solo un ejemplo, ajusta según tu modelo real
        
        db.session.commit()
        
        # Ejecutar el método
        service = FoodDatasetService()
        stats = service.get_all_statistics()
        
        # Verificar que tenemos datos
        assert "datasets_counter" in stats
        assert "food_models_counter" in stats
        assert "total_dataset_downloads" in stats
        assert "total_dataset_views" in stats
        assert isinstance(stats, dict)