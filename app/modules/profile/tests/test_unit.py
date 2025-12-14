import uuid
from datetime import datetime

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.basedataset.models import BaseDSMetaData, BaseDataset, BasePublicationType, BaseDatasetVersion
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        user_test = User(email="user@example.com", password="test1234", is_email_verified=True)
        db.session.add(user_test)
        db.session.commit()

        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

    yield test_client

@pytest.fixture
def user_with_datasets(test_client):
    unique_email = f"dataset_user_{uuid.uuid4()}@example.com"
    user = User(email=unique_email, password="pass1234")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(user_id=user.id, name="Test", surname="User")
    db.session.add(profile)

    for i in range(2):
        meta = FoodDSMetaData(
            title=f"Food Dataset {i}",
            description=f"Nutritional Data {i}",
            publication_type=BasePublicationType.JOURNAL_ARTICLE
        )
        db.session.add(meta)
        db.session.flush()
        dataset = FoodDataset(
            user_id=user.id,
            ds_meta_data_id=meta.id,
            view_count=10,
            download_count=5
        )
        db.session.add(dataset)
        db.session.flush()
        version = BaseDatasetVersion(
            dataset_id=dataset.id,
            version_number=f"1.{i}",
            title=meta.title,
            description=meta.description,
            created_by_id=user.id,
            version_type="base"
        )
        db.session.add(version)

    db.session.commit()
    yield user

def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get("/profile/edit")
    assert response.status_code == 200, "The profile editing page could not be accessed."
    assert b"Edit profile" in response.data, "The expected content is not present on the page"

    logout(test_client)


def test_user_profile_not_found(test_client):
    """
    Verifica que acceder a un perfil inexistente devuelve 404.
    """
    response = test_client.get("/profile/99999")  # ID que no existe
    assert response.status_code == 404, "Un perfil inexistente debería devolver 404."


def test_my_profile_authenticated(test_client, user_with_datasets):
    # Log in the user so current_user is populated
    with test_client.session_transaction() as sess:
        sess['user_id'] = user_with_datasets.id
    
    response = test_client.get("/profile/summary")
    assert response.status_code == 200 or response.status_code == 302


def test_user_profile_view(test_client, user_with_datasets):
    """
    Verifica que la vista /profile/<id> muestra correctamente
    el perfil y los BaseDatasets.
    """
    user_id = user_with_datasets.id
    response = test_client.get(f"/profile/{user_id}")
    
    assert response.status_code == 200, "La vista de perfil público no respondió con 200 OK."
    response_content = response.data.decode('utf-8')

    assert "Test" in response_content, "El nombre del perfil no aparece."
    assert "User" in response_content, "El apellido del perfil no aparece."
    assert "Food Dataset 0" in response_content or "BaseDataset 1" in response_content, \
        "Los BaseDatasets del usuario no aparecen en la página."
    

def test_user_profile_view2(test_client, user_with_datasets):
    """
    Test de diagnóstico para encontrar por qué da 404.
    """
    user_id = int(user_with_datasets.get_id())
    print("\n--- DIAGNÓSTICO ---")
    print(f"1. ID del usuario creado: {user_id}")
    
    # Comprobamos si el usuario existe en la DB ahora mismo
    with test_client.application.app_context():
        user_db = User.query.get(user_id)
        print(f"2. ¿Existe el usuario en DB antes de llamar al cliente?: {'SÍ' if user_db else 'NO'}")
        
        # Verificamos las rutas registradas para ver si hay prefijos raros
        print("3. Rutas registradas para 'profile':")
        for rule in test_client.application.url_map.iter_rules():
            if "profile" in str(rule):
                print(f"   - {rule}")

    target_url = f"/profile/{user_id}"
    print(f"4. Intentando acceder a: {target_url}")
    response = test_client.get(target_url)
    print(f"5. Código de estado obtenido: {response.status_code}")
    print("-------------------")
    assert response.status_code == 200
