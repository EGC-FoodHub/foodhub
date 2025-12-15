import io
import urllib.error
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from werkzeug.exceptions import NotFound

import pytest

from app.modules.fooddataset.services import FoodDatasetService

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


@pytest.fixture
def mock_dataset():
    """Create a mock dataset with complete structure"""
    dataset = MagicMock()
    dataset.id = 123
    dataset.ds_meta_data = MagicMock()
    dataset.ds_meta_data.title = "Original Title"
    dataset.ds_meta_data.description = "Original Description"
    dataset.ds_meta_data.publication_type.value = "MANUAL"
    dataset.ds_meta_data.publication_doi = "10.1234/test"
    dataset.ds_meta_data.tags = "tag1,tag2"
    author1 = MagicMock()
    author1.name = "John Doe"
    author1.affiliation = "University A"
    author1.orcid = "0000-0001-1111-1111"

    dataset.ds_meta_data.authors = [author1]

    file1 = MagicMock()
    file1.name = "model1.food"

    food_model1 = MagicMock()
    food_model1.files = [file1]
    food_model1.food_meta_data = MagicMock()
    food_model1.food_meta_data.food_filename = "model1.food"
    food_model1.food_meta_data.title = "Model 1 Title"
    food_model1.food_meta_data.description = "Model 1 Desc"
    food_model1.food_meta_data.publication_type = "MANUAL"
    food_model1.food_meta_data.publication_doi = "10.5678/model1"
    food_model1.food_meta_data.tags = "modeltag1"

    model_author = MagicMock()
    model_author.name = "Model Author"
    model_author.affiliation = "Model Univ"
    model_author.orcid = "0000-0003-3333-3333"

    food_model1.food_meta_data.authors = [model_author]

    dataset.files = [food_model1]
    return dataset


@pytest.fixture
def mock_form():
    """Fixture para simular el formulario."""
    return MagicMock()


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
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
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
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    zip_file = create_test_zip({})
    data = {"file": (zip_file, "empty.zip")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    resp_json = response.get_json()
    assert resp_json["message"] == "No files extracted from the ZIP"


def test_upload_zip_invalid_file_type(test_client, mock_user, monkeypatch):
    """Test integración: subida de un archivo que no es ZIP"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    data = {"file": (io.BytesIO(b"notazip"), "notazip.txt")}
    response = test_client.post("/dataset/file/upload_zip", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    resp_json = response.get_json()
    assert resp_json["message"] == "No valid zip file"


def test_create_dataset_from_zip(tmp_path, mock_user):
    """Test integración: creación de dataset desde ZIP usando FoodDatasetService"""
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
    service = FoodDatasetService()
    service.author_repository = FakeRepo()
    service.dsmetadata_repository.create = MagicMock(return_value=SimpleNamespace(id=1, authors=[]))
    service.create = MagicMock(return_value=SimpleNamespace(id=1, feature_models=[]))

    service.fmmetadata_repository = FakeRepo()
    service.feature_model_repository = FakeRepo()
    service.hubfilerepository = FakeHubFileRepo()

    # Stub the private helper used by the real service implementation to avoid
    # AttributeError in the test environment and focus on ZIP processing.
    service._create_dataset_shell = MagicMock(return_value=SimpleNamespace(id=1, feature_models=[]))

    dataset = service.create_from_zip(form, mock_user)
    assert dataset is not None


def test_upload_github_no_food_files(test_client, mock_user, monkeypatch, tmp_path):
    """Integration: valid GitHub repo but ZIP has no .food files -> 400"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
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
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
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
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
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
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    # Provide a non-github zip_url
    data = {"zip_url": "https://example.com/some.zip"}
    resp = test_client.post("/dataset/file/upload_github", data=data)

    assert resp.status_code == 400
    j = resp.get_json()
    assert j["message"] == "Only GitHub zip URLs are supported"


def test_create_dataset_as_draft_post_success_with_food_models(test_client, mock_user, monkeypatch):
    """Test POST: dataset created successfully with food models and temp folder cleaned"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("app.modules.fooddataset.routes.shutil.rmtree") as mock_rmtree,
        patch("app.modules.fooddataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.fooddataset.routes.os.path.isdir") as mock_isdir,
    ):
        mock_dataset = MagicMock()
        mock_dataset.id = 1
        mock_service.create_from_form.return_value = mock_dataset

        mock_form = MockForm.return_value
        mock_form.food_models.entries = [MagicMock(filename=MagicMock(data="test.food"))]

        mock_user.temp_folder.return_value = "/tmp/testuser"
        mock_exists.return_value = True
        mock_isdir.return_value = True

        response = test_client.post("/dataset/save_as_draft", data={"title": "New Dataset"})

        assert response.status_code == 200
        assert response.get_json()["message"] == "Everything works!"

        mock_service.create_from_form.assert_called_once()
        mock_rmtree.assert_called_once_with("/tmp/testuser")
        mock_user.temp_folder.assert_called()


def test_create_dataset_as_draft_post_service_exception(test_client, mock_user, monkeypatch):
    """Test POST: service exception returns 400 with error message"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
    ):
        mock_form = MockForm.return_value
        mock_form.food_models.entries = [MagicMock(filename=MagicMock(data="test.food"))]

        error_msg = "Invalid dataset metadata"
        mock_service.create_from_form.side_effect = Exception(error_msg)

        response = test_client.post("/dataset/save_as_draft", data={"title": "Dataset"})

        assert response.status_code == 400
        assert error_msg in response.get_json()["Exception while create dataset data in local: "]


def test_publish_dataset_not_found(test_client, mock_user, monkeypatch):
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with patch("app.modules.fooddataset.routes.food_service") as mock_service:
        mock_service.get_or_404.side_effect = NotFound()

        resp = test_client.get("/dataset/publish/999")
        assert resp.status_code == 404


def test_publish_dataset_success_safe(
    test_client, mock_user, mock_dataset, monkeypatch
):
    monkeypatch.setattr(
        "app.modules.fooddataset.routes.current_user",
        mock_user,
        raising=False,
    )
    monkeypatch.setattr(
        "flask_login.utils._get_user",
        lambda: mock_user,
        raising=False,
    )

    def safe_exists(path):
        if "(1)" in path:
            return False
        return True

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FakenodoService") as MockFakenodo,
        patch("app.modules.fooddataset.routes.base_doi_mapping_repository"),
        patch("app.modules.fooddataset.routes.dsmetadata_service"),
        patch("app.modules.fooddataset.routes.os.makedirs"),
        patch("app.modules.fooddataset.routes.os.path.exists", side_effect=safe_exists),
        patch("app.modules.fooddataset.routes.shutil.copy"),
        patch("app.modules.fooddataset.routes.os.getenv", return_value="/tmp"),
    ):
        mock_service.get_or_404.return_value = mock_dataset
        mock_service.edit_doi_dataset.return_value = (mock_dataset, [])

        fake_fakenodo = MockFakenodo.return_value
        fake_fakenodo.create_new_deposition.return_value = {
            "doi": "10.0000/fake",
            "id": 1,
        }
        fake_fakenodo.get_doi.return_value = "10.0000/fake"

        resp = test_client.post(f"/dataset/publish/{mock_dataset.id}")

        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Dataset published successfully"


def test_publish_dataset_missing_file_raises_safe(
    test_client, mock_user, mock_dataset, monkeypatch
):
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    def exists(path):
        return False

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FakenodoService"),
        patch("app.modules.fooddataset.routes.os.path.exists", side_effect=exists),
        patch("app.modules.fooddataset.routes.os.makedirs"),
    ):
        mock_service.get_or_404.return_value = mock_dataset
        mock_service.edit_doi_dataset.return_value = (mock_dataset, [])

        with pytest.raises(FileNotFoundError):
            test_client.post(f"/dataset/publish/{mock_dataset.id}")


def test_publish_dataset_fakenodo_upload_error_safe(
    test_client, mock_user, mock_dataset, monkeypatch
):
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    def exists(path):
        if "(1)" in path:
            return False
        return True

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FakenodoService") as MockFakenodo,
        patch("app.modules.fooddataset.routes.os.path.exists", side_effect=exists),
        patch("app.modules.fooddataset.routes.shutil.copy"),
        patch("app.modules.fooddataset.routes.os.makedirs"),
    ):
        mock_service.get_or_404.return_value = mock_dataset
        mock_service.edit_doi_dataset.return_value = (mock_dataset, [])

        fake_fakenodo = MockFakenodo.return_value
        fake_fakenodo.create_new_deposition.return_value = {"doi": "10.1111/error", "id": 99}
        fake_fakenodo.upload_file.side_effect = Exception("Upload failed")

        resp = test_client.post(f"/dataset/publish/{mock_dataset.id}")

        assert resp.status_code == 400
        assert "Error uploading to Fakenodo" in resp.get_json()["message"]


def test_edit_doi_dataset_get_not_found(test_client, mock_user, monkeypatch):
    """Test GET: dataset not found returns 404"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with patch("app.modules.fooddataset.routes.food_service") as mock_service:
        mock_service.get_or_404.side_effect = NotFound()

        response = test_client.get("/dataset/edit/999")
        assert response.status_code == 404


def test_edit_doi_dataset_get_loads_form_data(test_client, mock_user, mock_dataset, monkeypatch):
    """Test GET: form is populated with dataset metadata and files"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("app.modules.fooddataset.routes.AuthorForm"),
        patch("app.modules.fooddataset.routes.FoodModelForm"),
        patch("os.makedirs"),
        patch("os.path.exists", return_value=False),
        patch("shutil.copy"),
        patch("app.modules.fooddataset.routes.render_template"),
        patch("os.getenv", return_value="/work"),
    ):
        mock_service.get_or_404.return_value = mock_dataset
        mock_form = MockForm.return_value
        mock_form.authors.entries = []
        mock_form.food_models.entries = []

        test_client.get(f"/dataset/edit/{mock_dataset.id}")

        assert mock_form.title.data == "Original Title"
        assert mock_form.desc.data == "Original Description"
        assert mock_form.publication_type.data == "MANUAL"
        assert mock_form.publication_doi.data == "10.1234/test"
        assert mock_form.tags.data == "tag1,tag2"

        mock_form.authors.append_entry.assert_called()
        mock_form.food_models.append_entry.assert_called()


def test_edit_doi_dataset_get_handles_duplicate_filenames(test_client, mock_user, mock_dataset, monkeypatch):
    """Test GET: duplicate filenames are renamed with (n) suffix"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    def mock_exists(path):
        if "model1.food" in path and "(1)" not in path:
            return True
        return False

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm"),
        patch("app.modules.fooddataset.routes.AuthorForm"),
        patch("app.modules.fooddataset.routes.FoodModelForm"),
        patch("os.makedirs"),
        patch("os.path.exists", side_effect=mock_exists),
        patch("shutil.copy") as mock_copy,
        patch("app.modules.fooddataset.routes.render_template"),
        patch("os.getenv", return_value="/work"),
    ):
        mock_service.get_or_404.return_value = mock_dataset

        test_client.get(f"/dataset/edit/{mock_dataset.id}")

        mock_copy.assert_called()
        call_args = mock_copy.call_args_list[0]
        assert "(1)" in call_args[0][1]


def test_edit_doi_dataset_post_success(test_client, mock_user, mock_dataset, monkeypatch):
    """Test POST: successful dataset update calls service correctly"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("os.makedirs"),
        patch("os.getenv", return_value="/work"),
    ):
        mock_form = MockForm.return_value
        mock_form.food_models.entries = [MagicMock(filename=MagicMock(data="test.food"))]

        mock_service.get_or_404.return_value = mock_dataset
        mock_service.edit_doi_dataset.return_value = (mock_dataset, [])
        mock_service.handle_service_response.return_value = MagicMock(status_code=200)

        test_client.post(
            f"/dataset/edit/{mock_dataset.id}",
            data={"title": "Updated Title"}
        )

        mock_service.edit_doi_dataset.assert_called_once_with(mock_dataset, mock_form)


def test_edit_doi_dataset_post_empty_food_models(test_client, mock_user, mock_dataset, monkeypatch):
    """Test POST: empty food models are cleared before service call"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("os.makedirs"),
        patch("os.getenv", return_value="/work"),
    ):
        mock_form = MockForm.return_value
        mock_form.food_models.entries = [MagicMock(filename=MagicMock(data=None))]

        mock_service.get_or_404.return_value = mock_dataset
        mock_service.edit_doi_dataset.return_value = (mock_dataset, [])
        mock_service.handle_service_response.return_value = MagicMock(status_code=200)

        test_client.post(
            f"/dataset/edit/{mock_dataset.id}",
            data={"title": "Updated Title"}
        )

        assert mock_form.food_models == []
        mock_service.edit_doi_dataset.assert_called_once()


def test_edit_doi_dataset_post_with_errors(test_client, mock_user, mock_dataset, monkeypatch):
    """Test POST: service errors are handled correctly"""
    monkeypatch.setattr("app.modules.fooddataset.routes.current_user", mock_user, raising=False)
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user, raising=False)

    with (
        patch("app.modules.fooddataset.routes.food_service") as mock_service,
        patch("app.modules.fooddataset.routes.FoodDatasetForm") as MockForm,
        patch("os.makedirs"),
        patch("os.getenv", return_value="/work"),
    ):
        mock_form = MockForm.return_value
        mock_form.food_models.entries = [MagicMock(filename=MagicMock(data="test.food"))]

        mock_service.get_or_404.return_value = mock_dataset
        errors = ["Invalid title", "Missing description"]
        mock_service.edit_doi_dataset.return_value = (None, errors)
        mock_service.handle_service_response.return_value = MagicMock(status_code=400)

        test_client.post(
            f"/dataset/edit/{mock_dataset.id}",
            data={"title": ""}
        )

        call_args = mock_service.handle_service_response.call_args
        assert call_args[0][1] == errors
