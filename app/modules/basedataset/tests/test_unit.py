from unittest.mock import MagicMock, patch

import pytest

from app import db
from app.modules.basedataset.models import (
    BaseAuthor,
    BaseDataset,
    BaseDatasetVersion,
    BaseDSMetaData,
    BasePublicationType,
)
from app.modules.basedataset.services import BaseDatasetService, BaseDSViewRecordService
from app.modules.conftest import login


# --- Concrete implementation for Abstract BaseDataset for testing ---
class ConcreteDSMetaData(BaseDSMetaData):
    __tablename__ = "concrete_ds_meta_data"
    id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), primary_key=True)
    dataset = db.relationship("ConcreteDataset", back_populates="ds_meta_data", uselist=False)

    __mapper_args__ = {
        "polymorphic_identity": "concrete_ds_meta_data",
    }


class ConcreteDataset(BaseDataset):
    __tablename__ = "concrete_dataset"
    id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), primary_key=True)

    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("concrete_ds_meta_data.id"))
    ds_meta_data = db.relationship(
        "ConcreteDSMetaData", back_populates="dataset", uselist=False, foreign_keys=[ds_meta_data_id]
    )

    __mapper_args__ = {"polymorphic_identity": "concrete"}

    def get_all_files(self):
        return []

    def parse_uploaded_file(self, file_storage):
        pass

    def calculate_metrics(self):
        pass


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Get the user from conftest/DB and ensure verified
        # Assuming ID 1 or query by email
        from app.modules.auth.models import User

        user = User.query.filter_by(email="test@example.com").first()
        if user:
            user.is_email_verified = True
            db.session.commit()

        # Create a sample dataset
        # Note: We must create the metadata first or rely on relationship handling
        ds_metadata = ConcreteDSMetaData(
            title="Test Dataset",
            description="A description",
            publication_type=BasePublicationType.JOURNAL_ARTICLE,
            tags="tag1,tag2",
        )

        dataset = ConcreteDataset(user_id=user.id if user else 1, ds_meta_data=ds_metadata)

        db.session.add(dataset)
        db.session.commit()

    yield test_client


def test_normalize_publication_type_none(test_client):
    ds = ConcreteDataset()
    assert ds._normalize_publication_type() is None


def test_normalize_publication_type_enum(test_client):
    ds = ConcreteDataset()
    ds.ds_meta_data = MagicMock(publication_type=BasePublicationType.BOOK)
    assert ds._normalize_publication_type() == BasePublicationType.BOOK


def test_normalize_publication_type_string_value(test_client):
    ds = ConcreteDataset()
    ds.ds_meta_data = MagicMock(publication_type="article")
    assert ds._normalize_publication_type() == BasePublicationType.JOURNAL_ARTICLE


def test_normalize_publication_type_string_name(test_client):
    ds = ConcreteDataset()
    ds.ds_meta_data = MagicMock(publication_type="JOURNAL_ARTICLE")
    assert ds._normalize_publication_type() == BasePublicationType.JOURNAL_ARTICLE


def test_normalize_publication_type_invalid(test_client):
    ds = ConcreteDataset()
    ds.ds_meta_data = MagicMock(publication_type="invalid_type")
    assert ds._normalize_publication_type() is None


def test_get_file_total_size_for_human():
    # Use a mock since this is purely logic-based and doesn't need DB
    ds = ConcreteDataset()
    ds.get_file_total_size = MagicMock(return_value=500)
    assert ds.get_file_total_size_for_human() == "500 bytes"

    ds.get_file_total_size = MagicMock(return_value=1025)
    assert ds.get_file_total_size_for_human() == "1.0 KB"

    ds.get_file_total_size = MagicMock(return_value=1024**2 + 500)
    assert ds.get_file_total_size_for_human() == "1.0 MB"

    ds.get_file_total_size = MagicMock(return_value=1024**3 + 500)
    assert ds.get_file_total_size_for_human() == "1.0 GB"


def test_get_fakenodo_url_valid(test_client):
    ds = ConcreteDataset()
    ds.ds_meta_data = MagicMock(deposition_id=12345, dataset_doi="10.5281/fakenodo.12345")
    assert ds.get_fakenodo_url() == "https://fakenodo.org/record/12345"


def test_get_fakenodo_url_invalid(test_client):
    ds = ConcreteDataset()
    ds.ds_meta_data = None
    assert ds.get_fakenodo_url() is None

    ds.ds_meta_data = MagicMock(dataset_doi=None)
    assert ds.get_fakenodo_url() is None


def test_version_compare_metadata():
    v1 = BaseDatasetVersion(title="Old Title", description="Old Desc")
    v2 = BaseDatasetVersion(title="New Title", description="New Desc")

    diff = v2._compare_metadata(v1)

    assert "title" in diff
    assert diff["title"]["old"] == "Old Title"
    assert diff["title"]["new"] == "New Title"

    assert "description" in diff
    assert diff["description"]["old"] == "Old Desc"
    assert diff["description"]["new"] == "New Desc"


def test_version_compare_files():
    v1 = BaseDatasetVersion()
    v1.files_snapshot = {"file1.txt": {"checksum": "123", "size": 10}, "file2.txt": {"checksum": "abc", "size": 20}}

    v2 = BaseDatasetVersion()
    v2.files_snapshot = {
        "file1.txt": {"checksum": "123", "size": 10},  # Same
        "file2.txt": {"checksum": "xyz", "size": 25},  # Modified
        "file3.txt": {"checksum": "789", "size": 30},  # Added
    }

    diff = v2._compare_files(v1)

    assert "file3.txt" in diff["added"]
    assert "file2.txt" in diff["modified"]
    assert len(diff["removed"]) == 0

    # Reverse comparison to test removal
    diff_rev = v1._compare_files(v2)
    assert "file3.txt" in diff_rev["removed"]


def test_view_record_create_cookie(test_client):
    service = BaseDSViewRecordService()

    # Test creating a fresh cookie
    # Since we can't easily mock request context without app context, we use the client context
    with test_client.application.test_request_context():
        # Test 1: No existing cookie in request
        # We need a dummy dataset id. We can use one that we know won't crash DB lookups if mocked
        # But we are testing service logic which hits DB for 'the_record_exists'.
        # We should use a real dataset or mock the repository.
        # Let's mock the repository to avoid DB complexity for this specific test

        service.repository.the_record_exists = MagicMock(return_value=None)
        service.repository.create_new_record = MagicMock()

        dataset = ConcreteDataset(id=999)

        cookie = service.create_cookie(dataset)
        assert cookie is not None
        assert len(cookie) > 0
        service.repository.create_new_record.assert_called()

        # Test 2: Existing cookie
        # Mock request.cookies
        # Note: flask request is global, mocking it here is tricky inside context.
        # But create_cookie calls `request.cookies.get`.
        # We can pass environment to test_request_context

    with test_client.application.test_request_context(environ_base={"HTTP_COOKIE": "view_cookie=existing-cookie-123"}):
        service.repository.the_record_exists = MagicMock(return_value=True)  # Record exists

        cookie_existing = service.create_cookie(dataset)
        assert cookie_existing == "existing-cookie-123"
        # create_new_record should NOT be called again
        # Reset mock from previous call
        service.repository.create_new_record = MagicMock()
        service.create_cookie(dataset)
        service.repository.create_new_record.assert_not_called()


def test_route_list_datasets(test_client):
    """Test the list datasets route (authentication required)."""
    # Try without login
    response = test_client.get("/dataset/list")
    assert response.status_code == 302  # Redirect to login

    # Login
    login(test_client, "test@example.com", "test1234")
    response = test_client.get("/dataset/list")
    assert response.status_code == 200
    assert b"Datasets" in response.data


def test_route_view_dataset(test_client):
    """Test viewing a specific dataset."""
    login(test_client, "test@example.com", "test1234")

    # We need a valid ID. In our test_client fixture we created a ConcreteDataset.
    # However, Abstract/Concrete datasets might not appear in the specific query used by the route
    # if the route filters by specific types (FoodDataset) or if the template requires specific fields.
    # Route: dataset = dataset_service.get_by_id(dataset_id)
    # The `dataset_service` uses `BaseDatasetRepository` which queries `BaseDataset`.
    # So it should find our ConcreteDataset.

    # We need to find the ID of the dataset created in fixture.
    # Since we can't easily pass it out, we query it.
    with test_client.application.app_context():
        dataset = ConcreteDataset.query.first()
        ds_id = dataset.id

    response = test_client.get(f"/dataset/{ds_id}")
    assert response.status_code == 200
    assert b"Test Dataset" in response.data


def test_route_view_dataset_404(test_client):
    login(test_client, "test@example.com", "test1234")
    response = test_client.get("/dataset/999999")
    assert response.status_code == 404


def test_route_download_dataset_404(test_client):
    login(test_client, "test@example.com", "test1234")
    response = test_client.get("/dataset/download/999999")
    assert response.status_code == 404


def test_route_doi_redirection(test_client):
    response = test_client.get("/doi/10.1234/nonexistent/")
    assert response.status_code == 404


def test_size_service():
    from app.modules.basedataset.services import SizeService

    service = SizeService()
    assert service.get_human_readable_size(100) == "100 bytes"
    assert service.get_human_readable_size(2048) == "2.0 KB"


def test_dataset_file_methods(test_client):
    # Test internal logic of helper methods, mocking 'files' relationship
    ds = ConcreteDataset()
    # Mocking files list with objects having size_in_bytes
    f1 = MagicMock(size_in_bytes=100)
    f2 = MagicMock(size_in_bytes=200)
    ds.files = [f1, f2]

    assert ds.get_files_count() == 2
    assert ds.get_file_total_size() == 300


def test_version_to_dict(test_client):
    v = BaseDatasetVersion(version_number="1.0", title="T", description="D", changelog="C")
    # create_by is relationship, mock it if needed or check handle None
    d = v.to_dict()
    assert d["version_number"] == "1.0"
    assert d["title"] == "T"


def test_validate_upload(test_client):
    ds = ConcreteDataset()
    assert ds.validate_upload("path") is True
    assert ds.versioning_rules() == {}
    assert ds.specific_template() is None


def test_service_counts(test_client):
    service = BaseDatasetService()
    # These verify the passthrough to repositories
    # Since we have data in DB from fixture, counts should be >= 0
    assert service.count_authors() >= 0
    assert service.count_dsmetadata() >= 0
    assert service.total_dataset_downloads() >= 0
    assert service.total_dataset_views() >= 0


def test_route_download_dataset_success(test_client):
    login(test_client, "test@example.com", "test1234")

    # We need to mock filesystem operations to simulate a dataset existing on disk
    with (
        patch("app.modules.basedataset.routes.os.path.exists") as mock_exists,
        patch("app.modules.basedataset.routes.os.walk") as mock_walk,
        patch("app.modules.basedataset.routes.ZipFile") as mock_zip,
        patch("app.modules.basedataset.routes.send_from_directory") as mock_send,
    ):

        mock_exists.return_value = True
        mock_walk.return_value = [("/path", [], ["file.txt"])]

        # Mock send_from_directory to return a simple response
        mock_send.return_value = "File Content"

        # We need a valid dataset ID to avoid 404
        with test_client.application.app_context():
            dataset = ConcreteDataset.query.first()
            ds_id = dataset.id

        response = test_client.get(f"/dataset/download/{ds_id}")
        assert response.status_code == 200
        mock_zip.assert_called()


def test_route_doi_view_success(test_client):
    # Test valid DOI lookup logic
    # We need to ensure filter_by_doi finds a metadata which has a dataset
    with (
        patch("app.modules.basedataset.services.BaseDSMetaDataService.filter_by_doi") as mock_filter,
        patch("app.modules.basedataset.routes.ds_view_record_service") as mock_view_service,
    ):

        # Mock the metadata object and its dataset relationship
        mock_meta = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.id = 123
        mock_meta.dataset = mock_dataset
        mock_filter.return_value = mock_meta

        # Mock create_cookie to avoid DB usage
        mock_view_service.create_cookie.return_value = "cookie"

        # Mock render_template to avoid template errors with mocks
        with patch("app.modules.basedataset.routes.render_template") as mock_render:
            mock_render.return_value = "Rendered"

            response = test_client.get("/doi/10.1234/valid-doi/")
            assert response.status_code == 200
            assert b"Rendered" in response.data


def test_author_to_dict(test_client):
    author = BaseAuthor(name="A", affiliation="B", orcid="C")
    d = author.to_dict()
    assert d["name"] == "A"
    assert d["affiliation"] == "B"
    assert d["orcid"] == "C"


def test_dataset_delete(test_client):
    with test_client.application.app_context():
        # Create a temp dataset to delete
        ds = ConcreteDataset(user_id=1)
        db.session.add(ds)
        db.session.commit()
        ds_id = ds.id

        ds.delete()

        # Verify deletion
        assert ConcreteDataset.query.get(ds_id) is None


def test_route_doi_mapping_redirect(test_client):
    # Test DOI mapping redirect
    with patch("app.modules.basedataset.services.BaseDOIMappingService.get_new_doi") as mock_mapping:
        mock_mapping.return_value = "10.1234/new-doi"

        response = test_client.get("/doi/10.1234/old-doi/")
        assert response.status_code == 302
        assert "10.1234/new-doi" in response.headers["Location"]
