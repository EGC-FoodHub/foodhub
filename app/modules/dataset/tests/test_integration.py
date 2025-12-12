import io
import urllib.error
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.dataset.services import DataSetService

pytestmark = pytest.mark.integration


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


# backward-compatible alias (some tests use make_test_zip)
make_test_zip = create_test_zip


class FakeResp(io.BytesIO):
    """A small context-manager bytes response to mock urllib.request.urlopen."""

    def __init__(self, data: bytes, status=None):
        super().__init__(data)
        self.status = status

    def __enter__(self):
        self.seek(0)
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


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


class FakeHubFileRepo:
    def __init__(self):
        self.created = []
        self.counter = 1

    def create(self, commit=False, **kwargs):
        hub = SimpleNamespace(id=self.counter, **kwargs)
        self.counter += 1
        self.created.append(hub)
        return hub


# ------------------ INTEGRATION TESTS ------------------


def test_upload_zip_valid(test_client, mock_user, monkeypatch):
    """Test integración: subida de un ZIP válido con archivos .food"""
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
    """Test integración: subida de un ZIP vacío"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    zip_file = create_test_zip({})
    data = {"file": (zip_file, "empty.zip")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    resp_json = response.get_json()
    assert resp_json["message"] == "No files extracted from the ZIP"


def test_upload_zip_invalid_file_type(test_client, mock_user, monkeypatch):
    """Test integración: subida de un archivo que no es ZIP"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    data = {"file": (io.BytesIO(b"notazip"), "notazip.txt")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    resp_json = response.get_json()
    assert resp_json["message"] == "No valid zip file"


def test_create_dataset_from_zip(tmp_path, mock_user):
    """Test integración: creación de dataset desde ZIP usando DataSetService"""
    test_files = {"fm1.food": "dummy1", "fm2.food": "dummy2"}
    zip_file = create_test_zip(test_files)

    # Mock del formulario que recibiría el ZIP y metadatos
    form = MagicMock()
    form.zip_file.data = zip_file
    form.get_dsmetadata.return_value = {
        "title": "Test Dataset",
        "description": "Test Desc",
        "publication_type": "MANUAL",
    }
    form.get_authors.return_value = []

    # Inicializamos el servicio con repositorios fake
    service = DataSetService()
    service.author_repository = FakeRepo()
    service.dsmetadata_repository.create = MagicMock(return_value=SimpleNamespace(id=1, authors=[]))
    service.create = MagicMock(return_value=SimpleNamespace(id=1, feature_models=[]))

    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeRepo()
    service.hubfilerepository = FakeHubFileRepo()

    dataset = service.create_from_zip(form, mock_user)
    assert dataset is not None


def test_upload_github_no_food_files(test_client, mock_user, monkeypatch, tmp_path):
    """Integration: valid GitHub repo but ZIP has no .food files -> 400"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    zipbuf = make_test_zip({"README.md": "no food"})

    def fake_urlopen(url):
        return FakeResp(zipbuf.getvalue())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    data = {"repo": "user/repo"}
    resp = test_client.post("/dataset/file/upload_github", data=data)

    # The route extracts all files (not only .food), so README.md will be returned
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["message"] == "GitHub repo extracted successfully"


def test_upload_github_invalid_branch(test_client, mock_user, monkeypatch):
    """Integration: GitHub zip download returns 404 -> 400 with not found message"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    def fake_urlopen(url):
        raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    data = {"repo": "user/repo", "branch": "nope"}
    resp = test_client.post("/dataset/file/upload_github", data=data)

    assert resp.status_code == 400
    j = resp.get_json()
    assert j["message"] == "GitHub repository or Branch not found"


def test_upload_github_with_food_file(test_client, mock_user, monkeypatch, tmp_path):
    """Integration: GitHub repo zip contains .food file -> success and filenames returned"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    zipbuf = make_test_zip({"path/model.food": "content"})

    def fake_urlopen(url):
        return FakeResp(zipbuf.getvalue())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    data = {"repo": "user/repo"}
    resp = test_client.post("/dataset/file/upload_github", data=data)

    assert resp.status_code == 200
    j = resp.get_json()
    assert "filenames" in j
    assert any(f.endswith(".food") for f in j["filenames"])


def test_upload_github_invalid_url_provided(test_client, mock_user, monkeypatch):
    """Integration: provide a zip_url that is not a GitHub URL -> 400"""
    monkeypatch.setattr("app.modules.dataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    # Provide a non-github zip_url
    data = {"zip_url": "https://example.com/some.zip"}
    resp = test_client.post("/dataset/file/upload_github", data=data)

    assert resp.status_code == 400
    j = resp.get_json()
    assert j["message"] == "Only GitHub zip URLs are supported"
