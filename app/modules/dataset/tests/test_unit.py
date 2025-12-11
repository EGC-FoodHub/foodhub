import io
import logging
import uuid
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app import create_app
from app.modules.dataset.services import DataSetService

# ------------------ FIXTURES ------------------


@pytest.fixture(scope="module")
def test_client():
    app = create_app("testing")
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.profile.surname = "Doe"
    user.profile.name = "John"
    user.profile.affiliation = "Test University"
    user.profile.orcid = "0000-0000-0000-0000"
    user.temp_folder.return_value = "/tmp/testuser"
    user.is_authenticated = True
    return user


# ------------------ HELPERS ------------------


def create_test_zip(files: dict) -> io.BytesIO:
    """Crea un zip en memoria con archivos dados."""
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    zip_bytes.seek(0)
    return zip_bytes


# ------------------ FAKE REPOS ------------------


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


# ------------------ UNIT TESTS ------------------


def test_process_zip_extracts_food_files_only(tmp_path):
    """_process_zip_file extrae solo archivos .food y los registra en hubfilerepository"""
    service = DataSetService()
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
    service = DataSetService()
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    bad = io.BytesIO(b"not a zip")
    with pytest.raises(ValueError):
        service._process_zip_file(SimpleNamespace(id=1), bad, current_user)


def test_process_zip_no_matching_files_logs_warning(tmp_path, caplog):
    service = DataSetService()
    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeFeatureModelRepo()
    service.hubfilerepository = FakeHubFileRepo()

    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    zipbuf = create_test_zip({"readme.md": "hello"})

    caplog.set_level(logging.WARNING)
    service._process_zip_file(SimpleNamespace(id=3), zipbuf, current_user)

    assert any("No .food files found" in rec.getMessage() for rec in caplog.records)


# ------------------ INTEGRATION TESTS ------------------


def test_upload_zip_valid(test_client, mock_user, monkeypatch):
    # Mock usuario actual
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    test_files = {"file1.food": "content1", "file2.food": "content2"}
    zip_file = create_test_zip(test_files)

    data = {"file": (zip_file, "test.zip")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    resp_json = response.get_json()
    assert all(fname.endswith(".food") for fname in resp_json["filenames"])
    assert len(resp_json["filenames"]) == len(test_files)


def test_upload_zip_empty(test_client, mock_user, monkeypatch):
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    zip_file = create_test_zip({})
    data = {"file": (zip_file, "empty.zip")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    resp_json = response.get_json()
    assert resp_json["message"] == "No files extracted from the ZIP"


def test_upload_zip_invalid_file_type(test_client, mock_user, monkeypatch):
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    data = {"file": (io.BytesIO(b"notazip"), "notazip.txt")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    resp_json = response.get_json()
    assert resp_json["message"] == "No valid zip file"


def test_create_dataset_from_zip(tmp_path, mock_user):
    test_files = {"fm1.food": "dummy1", "fm2.food": "dummy2"}
    zip_file = create_test_zip(test_files)

    form = MagicMock()
    form.zip_file.data = zip_file
    form.get_dsmetadata.return_value = {
        "title": "Test Dataset",
        "description": "Test Desc",
        "publication_type": "MANUAL",
    }
    form.get_authors.return_value = []

    service = DataSetService()
    service.author_repository = FakeRepo()
    service.dsmetadata_repository.create = MagicMock(return_value=SimpleNamespace(id=1, authors=[]))
    service.create = MagicMock(return_value=SimpleNamespace(id=1, feature_models=[]))

    service.fmmetadata_repository.create = MagicMock(
        side_effect=lambda **kwargs: SimpleNamespace(id=uuid.uuid4().int, authors=[])
    )
    service.feature_model_repository.create = MagicMock(
        side_effect=lambda **kwargs: SimpleNamespace(id=uuid.uuid4().int, files=[])
    )
    service.hubfilerepository.create = FakeHubFileRepo().create

    dataset = service.create_from_zip(form, mock_user)
    assert dataset is not None