import pytest
import uuid

from datetime import datetime
from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.basedataset.models import BaseDSMetaData, BaseDataset, BasePublicationType


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
def user_with_BaseDatasets(test_client):
    user_id = None
    
    with test_client.application.app_context():

        unique_email = f"BaseDataset_user_{uuid.uuid4()}@example.com"
        user = User(email=unique_email, password="pass1234")
        db.session.add(user)
        db.session.commit()
        
        user_id = user.id
        profile = UserProfile(user_id=user_id, name="Test", surname="User")
        db.session.add(profile)

        for i in range(2):
            meta = BaseDSMetaData(
                title=f"BaseDataset {i}", 
                description=f"Desc {i}",
                publication_type=BasePublicationType.JOURNAL_ARTICLE,
                tags="test"
            )
            db.session.add(meta)
            db.session.flush() 

            BaseDataset = BaseDataset(
                user_id=user_id, 
                ds_meta_data_id=meta.id, 
                created_at=datetime.utcnow()
            )
            db.session.add(BaseDataset)

        db.session.commit()

    yield user_id

    with test_client.application.app_context():
        if user_id:
            BaseDataset.query.filter_by(user_id=user_id).delete()
            UserProfile.query.filter_by(user_id=user_id).delete()
            User.query.filter_by(id=user_id).delete()
            db.session.commit()
            db.session.remove()


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


def test_user_profile_view(test_client, user_with_BaseDatasets):
    """
    Verifica que la vista /profile/<id> muestra correctamente
    el perfil y los BaseDatasets.
    """
    user_id = user_with_BaseDatasets
    response = test_client.get(f"/profile/{user_id}")
    
    assert response.status_code == 200, "La vista de perfil público no respondió con 200 OK."
    response_content = response.data.decode('utf-8')

    assert "Test" in response_content, "El nombre del perfil no aparece."
    assert "User" in response_content, "El apellido del perfil no aparece."


    assert "BaseDataset 0" in response_content or "BaseDataset 1" in response_content, \
        "Los BaseDatasets del usuario no aparecen en la página."
    

def test_user_profile_view2(test_client, user_with_BaseDatasets):
    """
    Test de diagnóstico para encontrar por qué da 404.
    """
    user_id = user_with_BaseDatasets
    print(f"\n--- DIAGNÓSTICO ---")
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
