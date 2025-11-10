import pytest
import json
from app import create_app
from flask import Response

@pytest.fixture(scope="module")
def test_client():
    """
    Crea un cliente de pruebas de Flask para el módulo fakenodo.
    """
    app = create_app("testing")
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client



"""
Test positivos
"""

def test_create_record(test_client):
    data = {
        "metadata": {"title": "Test Record", "author": "Tester"},
        "files": []
    }

    response = test_client.post(
        "/fakenodo/records",
        data=json.dumps(data),
        content_type="application/json"
    )

    assert response.status_code == 201
    record = response.get_json()
    assert "id" in record
    assert "doi" in record
    assert record["metadata"]["title"] == "Test Record"


def test_get_records(test_client):
    response = test_client.get("/fakenodo/records")
    assert response.status_code == 200
    records = response.get_json()
    assert isinstance(records, list)
    assert len(records) > 0


def test_get_record_by_id(test_client):
    all_records = test_client.get("/fakenodo/records").get_json()
    record_id = all_records[0]["id"]

    response = test_client.get(f"/fakenodo/records/{record_id}")
    assert response.status_code == 200
    record = response.get_json()
    assert record["id"] == record_id


def test_update_record_metadata(test_client):
    all_records = test_client.get("/fakenodo/records").get_json()
    record_id = all_records[0]["id"]

    update_data = {"metadata": {"title": "Updated Title"}}
    response = test_client.put(
        f"/fakenodo/records/{record_id}",
        data=json.dumps(update_data),
        content_type="application/json"
    )

    assert response.status_code == 200
    updated = response.get_json()
    assert updated["metadata"]["title"] == "Updated Title"


def test_add_files_to_record(test_client):
    all_records = test_client.get("/fakenodo/records").get_json()
    record_id = all_records[0]["id"]

    files_data = {"files": [{"filename": "test.txt", "size": "1KB"}]}
    response = test_client.post(
        f"/fakenodo/records/{record_id}/files",
        data=json.dumps(files_data),
        content_type="application/json"
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["status"] == "files added"
    assert any(f["filename"] == "test.txt" for f in result["files"])


def test_publish_record(test_client):
    all_records = test_client.get("/fakenodo/records").get_json()
    record_id = all_records[0]["id"]

    response = test_client.post(f"/fakenodo/records/{record_id}/publish")
    assert response.status_code == 201
    published = response.get_json()
    assert published["published"] is True
    assert published["version"] > 1

"""
Test negativos
"""

def test_get_nonexistent_record(test_client):
    response = test_client.get("/fakenodo/records/invalid123")
    assert response.status_code == 404
    error = response.get_json()
    assert "error" in error
    assert error["error"] == "Record not found"


def test_update_nonexistent_record(test_client):
    update = {"metadata": {"title": "Should Fail"}}
    response = test_client.put(
        "/fakenodo/records/nonexistent",
        data=json.dumps(update),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Record not found"


def test_publish_nonexistent_record(test_client):
    response = test_client.post("/fakenodo/records/fakeid/publish")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Record not found"


def test_add_files_to_nonexistent_record(test_client):
    data = {"files": [{"filename": "ghost.txt"}]}
    response = test_client.post(
        "/fakenodo/records/notreal/files",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Record not found"


def test_post_invalid_content_type(test_client):
    response = test_client.post("/fakenodo/records", data="not json data")
    assert response.status_code == 415