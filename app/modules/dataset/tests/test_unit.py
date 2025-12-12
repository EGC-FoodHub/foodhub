import io
import logging
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock
import requests

import pytest

from app import create_app
from app.modules.dataset.services import DataSetService

pytestmark = pytest.mark.unit


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


# ------------------ GITHUB UPLOAD MINIMAL TESTS ------------------


def make_form(url: str):
    return SimpleNamespace(github_url=SimpleNamespace(data=url))


def test_create_from_github_success(monkeypatch, tmp_path):
    """Caso mínimo: descarga correcta y se llama a _process_zip_file"""
    service = DataSetService()
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
    service = DataSetService()
    service._create_dataset_shell = MagicMock(return_value=SimpleNamespace(id=1))
    service._process_zip_file = MagicMock()
    service.repository.session = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    form = make_form("https://notgithub.com/user/repo")
    current_user = SimpleNamespace()
    current_user.temp_folder = lambda: str(tmp_path)

    with pytest.raises(ValueError):
        service.create_from_github(form, current_user)


def test_create_from_github_no_food_files(monkeypatch, tmp_path, caplog):
    """Valid GitHub URL but ZIP contains no .food files: should commit and create no hubfiles."""
    service = DataSetService()
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
    service = DataSetService()
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
    service = DataSetService()
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
