import pytest

from flask_login import current_user, login_user

from app.modules.conftest import login, logout
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, DSMetrics, PublicationType, Author
from datetime import datetime, timezone

from app import db



@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        user = User(email="test@test.com", password="123")
        db.session.add(user)

        create_test_dataset(user_id=1)

        db.session.commit()

        test_client.user_id = user.id

    yield test_client


def test_get_shopping_cart_from_current_user(test_client):
    user_id = test_client.user_id

    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)

    response = test_client.get("/shopping_cart")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "shopping_cart" in html

def test_add_dataset_to_cart(test_client):
    dataset = DataSet.query.first()
    dataset_id = dataset.id

    response = test_client.get("/shopping_cart")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    initial_dataset_size = html.count("dataset")
        
    response = test_client.get(f"/shopping_cart/add/{dataset_id}")
    assert response.status_code == 302
    response = test_client.get("/shopping_cart")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    end_dataset_size = html.count("dataset")
    
    assert end_dataset_size >= initial_dataset_size
    
def test_remove_dataset_from_cart(test_client):
    dataset = DataSet.query.first()
    dataset_id = dataset.id

    response = test_client.get("/shopping_cart")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    initial_dataset_size = html.count("dataset")
        
    response = test_client.get(f"/shopping_cart/remove/{dataset_id}")
    assert response.status_code == 200
    response = test_client.get("/shopping_cart")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    end_dataset_size = html.count("dataset")
    
    assert end_dataset_size <= initial_dataset_size
    
    
def create_test_dataset(user_id=1):
    """
    Crea un dataset de prueba con metadata mínima y lo guarda en la DB de tests.
    Retorna el objeto DataSet.
    """
    ds_metrics = DSMetrics(number_of_models="1", number_of_features="10")
    db.session.add(ds_metrics)
    db.session.commit()

    ds_meta = DSMetaData(
        deposition_id=999,
        title="Test Dataset",
        description="This is a test dataset",
        publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
        publication_doi="10.1234/testdoi",
        dataset_doi="10.1234/testdataset",
        tags="test",
        ds_metrics_id=ds_metrics.id
    )
    db.session.add(ds_meta)
    db.session.commit()

    author = Author(
        name="Test Author",
        affiliation="Test Affiliation",
        orcid="0000-0000-0000-0000",
        ds_meta_data_id=ds_meta.id
    )
    db.session.add(author)
    db.session.commit()

    dataset = DataSet(
        user_id=user_id,
        ds_meta_data_id=ds_meta.id,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(dataset)
    db.session.commit()

    return dataset
