import pytest

from datetime import datetime
from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DSMetaData, DataSet, PublicationType


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        user_test = User(email="user@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

    yield test_client

@pytest.fixture
def user_with_datasets(test_client):
    """
    Crea un usuario con perfil y datasets reales (con DSMetaData)
    para probar la vista /profile/<id>.
    """
    with test_client.application.app_context():
        # Crear usuario y perfil
        user = User(email="dataset_user@example.com", password="pass1234")
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(user_id=user.id, name="Test", surname="User")
        db.session.add(profile)
        db.session.commit()

        # Crear datasets con metadatos asociados
        for i in range(3):
            meta = DSMetaData(
                title=f"Dataset {i}",
                description=f"Descripción del dataset {i}",
                publication_type=PublicationType.JOURNAL_ARTICLE, 
                deposition_id=None,
                dataset_doi=None,
                publication_doi=None,
                tags="test,pytest",
            )
            db.session.add(meta)
            db.session.flush()  # para obtener meta.id antes de usarlo

            dataset = DataSet(
                user_id=user.id,
                ds_meta_data_id=meta.id,
                created_at=datetime.utcnow(),
            )
            db.session.add(dataset)

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


def test_user_profile_view(test_client, user_with_datasets):
    """
    Verifica que la vista /profile/<id> muestra correctamente
    el perfil y los datasets de un usuario público.
    """
    user = user_with_datasets

    response = test_client.get(f"/profile/{user.id}")
    assert response.status_code == 200, "La vista de perfil público no respondió con 200 OK."

    # Comprobamos que el perfil se renderiza correctamente
    assert b"Test" in response.data, "El nombre del perfil no aparece en la página."
    assert b"User" in response.data, "El apellido del perfil no aparece en la página."

    # Verificamos que los datasets aparecen
    assert b"Dataset 0" in response.data or b"Dataset 1" in response.data, \
        "Los datasets del usuario no aparecen en la página."


def test_user_profile_not_found(test_client):
    """
    Verifica que acceder a un perfil inexistente devuelve 404.
    """
    response = test_client.get("/profile/99999")  # ID que no existe
    assert response.status_code == 404, "Un perfil inexistente debería devolver 404."
