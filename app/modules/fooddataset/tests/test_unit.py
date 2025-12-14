from unittest.mock import MagicMock, patch

import pytest
from types import SimpleNamespace
import zipfile
import io
import logging

import requests
from app import db
from app.modules.auth.models import User
from app.modules.basedataset.models import BaseAuthor, BasePublicationType
from app.modules.fooddataset.services import FoodDatasetService
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


def test_service_get_uvlhub_doi(test_client):
    from app.modules.fooddataset.services import FoodDatasetService

    service = FoodDatasetService()

    dataset = MagicMock()
    dataset.ds_meta_data.dataset_doi = "10.1234/test"

    # helper to mock env if needed, but default is localhost
    doi_url = service.get_uvlhub_doi(dataset)
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
        patch("app.modules.fooddataset.routes.FakenodoService") as MockFakenodo,
        patch("app.modules.fooddataset.routes.shutil.rmtree") as mock_rmtree,
        patch("app.modules.fooddataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("app.modules.auth.models.User.temp_folder") as mock_temp_folder,
    ):

        mock_dataset = MagicMock()
        mock_dataset.id = 1
        mock_dataset.files = []
        mock_service_instance.create_from_form.return_value = mock_dataset

        mock_fakenodo_instance = MockFakenodo.return_value
        mock_fakenodo_instance.create_new_deposition.return_value = {"id": 123, "conceptrecid": 456}

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


def test_route_dataset_upload_fakenodo_failure(test_client):
    from app.modules.conftest import login

    login(test_client, "test_food@example.com", "test1234")

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service_instance,
        patch("app.modules.fooddataset.routes.FakenodoService") as MockFakenodo,
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

        # Fakenodo failure
        mock_fakenodo_instance = MockFakenodo.return_value
        mock_fakenodo_instance.create_new_deposition.side_effect = Exception("Fakenodo Down")

        mock_exists.return_value = True
        mock_temp_folder.return_value = "/tmp"

        mock_form_instance = MockForm.return_value
        mock_form_instance.validate_on_submit.return_value = True

        # Should still return 200 but maybe with a warning or just success message
        # (Current implementation swallows Fakenodo errors and returns success)
        response = test_client.post("/dataset/upload", data={"title": "Test Title"})

        assert response.status_code == 200
        assert response.json["message"] == "Dataset created successfully!"
        # Verify Fakenodo was attempted
        mock_fakenodo_instance.create_new_deposition.assert_called()
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


def create_test_zip(files: dict) -> io.BytesIO:
    """Crea un zip en memoria con archivos dados."""
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    zip_bytes.seek(0)
    return zip_bytes


class FakeRepo:
    def __init__(self):
        self.created = []
        self.counter = 1

    def create(self, commit=False, **kwargs):
        obj = SimpleNamespace(**kwargs)
        obj.id = self.counter
        self.counter += 1
        self.created.append(obj)
        return obj


class FakeFeatureModelRepo:
    def __init__(self):
        self.created = []
        self.counter = 1

    def create(self, commit=False, data_set_id=None, fm_meta_data_id=None):
        fm = SimpleNamespace(id=self.counter, files=[])
        self.counter += 1
        self.created.append(fm)
        return fm


class FakeHubFileRepo:
    def __init__(self):
        self.created = []
        self.counter = 1

    def create(self, commit=False, **kwargs):
        hub = SimpleNamespace(id=self.counter, **kwargs)
        self.counter += 1
        self.created.append(hub)
        return hub


def test_process_zip_extracts_food_files_only(tmp_path):
    """_process_zip_file extrae solo archivos .food y los registra en hubfilerepository"""
    service = FoodDatasetService()
    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeFeatureModelRepo()
    service.hubfilerepository = FakeHubFileRepo()

    current_user = SimpleNamespace()
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    current_user.temp_folder = lambda: str(temp_dir)

    dataset = SimpleNamespace(id=42)

    files = {
        "model1.uvl": "uvl content",
        "nested/model2.food": "food content",
        "__MACOSX/._ignored.food": "should be ignored",
        "notes.txt": "ignore me",
    }

    zipbuf = create_test_zip(files)

    service._process_zip_file(dataset, zipbuf, current_user)

    # Solo debe haber sido extraído el .food correcto
    extracted = [p.name for p in temp_dir.iterdir()]
    assert "model2.food" in extracted
    assert "model1.uvl" not in extracted

    # Hubfile repo tiene registro
    assert len(service.hubfilerepository.created) == 1
    created = service.hubfilerepository.created[0]
    assert created.name == "model2.food"


def test_process_zip_invalid_raises(tmp_path):
    service = FoodDatasetService()
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    bad = io.BytesIO(b"not a zip")
    with pytest.raises(ValueError):
        service._process_zip_file(SimpleNamespace(id=1), bad, current_user)


def test_process_zip_no_matching_files_logs_warning(tmp_path, caplog):
    service = FoodDatasetService()
    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeFeatureModelRepo()
    service.hubfilerepository = FakeHubFileRepo()

    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    zipbuf = create_test_zip({"readme.md": "hello"})

    caplog.set_level(logging.WARNING)
    service._process_zip_file(SimpleNamespace(id=3), zipbuf, current_user)

    assert any("No .food files found" in rec.getMessage() for rec in caplog.records)


def make_form(url: str):
    return SimpleNamespace(github_url=SimpleNamespace(data=url))


def test_create_from_github_success(monkeypatch, tmp_path):
    """Caso mínimo: descarga correcta y se llama a _process_zip_file"""
    service = FoodDatasetService()
    fake_dataset = SimpleNamespace(id=99)
    service._create_dataset_shell = MagicMock(return_value=fake_dataset)
    service._process_zip_file = MagicMock()
    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    # Simular requests.get: repo info and zip
    def fake_get(url, *args, **kwargs):
        if url.startswith("https://api.github.com/"):
            m = MagicMock()
            m.json.return_value = {"default_branch": "main"}
            m.raise_for_status = MagicMock()
            return m
        elif url.endswith(".zip"):
            m = MagicMock()
            m.content = b"PK\x03\x04fakezip"
            m.raise_for_status = MagicMock()
            return m
        raise RuntimeError("Unexpected URL")

    monkeypatch.setattr("app.modules.dataset.services.requests.get", fake_get)

    form = make_form("https://github.com/user/repo")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    result = service.create_from_github(form, current_user)

    assert result is fake_dataset
    service._process_zip_file.assert_called_once()


def test_create_from_github_invalid_url_raises(tmp_path):
    service = FoodDatasetService()
    service._create_dataset_shell = MagicMock(return_value=SimpleNamespace(id=1))
    service._process_zip_file = MagicMock()
    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    form = make_form("https://notgithub.com/user/repo")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    with pytest.raises(ValueError):
        service.create_from_github(form, current_user)


def test_create_from_github_malformed_url_raises(tmp_path):
    """URL pointing to github but missing repo part should raise ValueError"""
    service = FoodDatasetService()
    service._create_dataset_shell = MagicMock(return_value=SimpleNamespace(id=2))
    service._process_zip_file = MagicMock()
    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    # github.com/user (no repo) -> invalid
    form = make_form("https://github.com/onlyuser")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: "/tmp"

    with pytest.raises(ValueError):
        service.create_from_github(form, current_user)


def test_create_from_github_no_food_files(monkeypatch, tmp_path, caplog):
    """Valid GitHub URL but ZIP contains no .food files: should commit and create no hubfiles."""
    service = FoodDatasetService()
    fake_dataset = SimpleNamespace(id=200)
    service._create_dataset_shell = MagicMock(return_value=fake_dataset)

    # use fake repos so that _process_zip_file can create objects without DB
    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeFeatureModelRepo()
    service.hubfilerepository = FakeHubFileRepo()

    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    # create zip with no .food files
    zipbuf = create_test_zip({"README.md": "no food here"})

    def fake_get(url, *args, **kwargs):
        if url.startswith("https://api.github.com/"):
            m = MagicMock()
            m.json.return_value = {"default_branch": "main"}
            m.raise_for_status = MagicMock()
            return m
        elif url.endswith(".zip"):
            m = MagicMock()
            m.content = zipbuf.getvalue()
            m.raise_for_status = MagicMock()
            return m
        raise RuntimeError("Unexpected URL")

    monkeypatch.setattr("app.modules.dataset.services.requests.get", fake_get)

    form = make_form("https://github.com/user/repo")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    caplog.set_level(logging.WARNING)
    result = service.create_from_github(form, current_user)

    assert result is fake_dataset
    # no hubfiles created
    assert len(service.hubfilerepository.created) == 0


def test_create_from_github_invalid_branch_raises(monkeypatch, tmp_path):
    """If zip download fails (invalid branch) raise ValueError"""
    service = FoodDatasetService()
    service._create_dataset_shell = MagicMock(return_value=SimpleNamespace(id=10))
    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    def fake_get(url, *args, **kwargs):
        if url.startswith("https://api.github.com/"):
            m = MagicMock()
            m.json.return_value = {"default_branch": "nonexistent"}
            m.raise_for_status = MagicMock()
            return m
        elif url.endswith(".zip"):
            # simulate 404 / requests exception when fetching zip
            raise requests.RequestException("Not Found")
        raise RuntimeError("Unexpected URL")

    monkeypatch.setattr("app.modules.dataset.services.requests.get", fake_get)

    form = make_form("https://github.com/user/repo")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    with pytest.raises(ValueError):
        service.create_from_github(form, current_user)


def test_create_from_github_with_food_files(monkeypatch, tmp_path):
    """Simulate github repo (EGC-FoodHub/foodhub main) with a .food file inside zip."""
    service = FoodDatasetService()
    fake_dataset = SimpleNamespace(id=300)
    service._create_dataset_shell = MagicMock(return_value=fake_dataset)

    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeFeatureModelRepo()
    service.hubfilerepository = FakeHubFileRepo()

    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    # zip with a .food file
    zipbuf = create_test_zip({"models/model.food": "food content"})

    def fake_get(url, *args, **kwargs):
        if url.startswith("https://api.github.com/repos/EGC-FoodHub/foodhub"):
            m = MagicMock()
            m.json.return_value = {"default_branch": "main"}
            m.raise_for_status = MagicMock()
            return m
        elif url.endswith("main.zip") or url.endswith(".zip"):
            m = MagicMock()
            m.content = zipbuf.getvalue()
            m.raise_for_status = MagicMock()
            return m
        raise RuntimeError("Unexpected URL")

    monkeypatch.setattr("app.modules.dataset.services.requests.get", fake_get)

    form = make_form("https://github.com/EGC-FoodHub/foodhub")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    result = service.create_from_github(form, current_user)

    assert result is fake_dataset
    # hubfile should have been created for model.food
    assert len(service.hubfilerepository.created) == 1
    assert service.hubfilerepository.created[0].name == "model.food"


def test_upload_file_valid(test_client, mock_user, monkeypatch, tmp_path):
    """Upload a single .food file via the route should return 200 and filename"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    # ensure temp folder exists
    temp_dir = tmp_path / "temp_user"
    temp_dir.mkdir()
    mock_user.temp_folder.return_value = str(temp_dir)

    data = {"file": (io.BytesIO(b"dummy content"), "test.food")}
    resp = test_client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

    assert resp.status_code == 200
    j = resp.get_json()
    assert j["message"] == "UVL uploaded and validated successfully"
    assert j["filename"] == "test.food"


def test_upload_file_invalid_extension(test_client, mock_user, monkeypatch, tmp_path):
    """Upload a non-.food file should be rejected with 400"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    temp_dir = tmp_path / "temp_user2"
    temp_dir.mkdir()
    mock_user.temp_folder.return_value = str(temp_dir)

    data = {"file": (io.BytesIO(b"not food"), "bad.txt")}
    resp = test_client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

    assert resp.status_code == 400
    j = resp.get_json()
    assert j["message"] == "Please upload a .food file"
