from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService


class TestAuthRegistration:

    @pytest.fixture(scope="module")
    def auth_service(self):
        return AuthenticationService()

    def test_create_with_profile_success(self, auth_service):
        user_data = {"email": "new@example.com", "password": "password123", "name": "John", "surname": "Doe"}

        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "new@example.com"

        with patch.object(auth_service, "create", return_value=mock_user) as mock_create:
            with patch.object(auth_service.user_profile_repository, "create") as mock_profile_create:
                with patch("app.modules.auth.services.generate_verification_token", return_value="token123"):
                    with patch("app.modules.auth.services.send_email_verification") as mock_send_email:
                        with patch.object(auth_service.repository.session, "commit"):
                            result = auth_service.create_with_profile(**user_data)
                            print(mock_profile_create.call_args_list)

                            assert result == mock_user
                            mock_create.assert_called_once_with(
                                commit=False, email="new@example.com", password="password123"
                            )
                            mock_profile_create.assert_called_once_with(
                                user_id=1,
                                name="John",
                                surname="Doe",
                                uploaded_datasets_count=0,
                                downloaded_datasets_count=0,
                                synchronized_datasets_count=0,
                            )
                            mock_send_email.assert_called_once_with(mock_user)

    def test_create_with_profile_missing_email(self, auth_service, test_client):
        with test_client.application.app_context():
            with pytest.raises(ValueError, match="Email is required."):
                auth_service.create_with_profile(password="pass", name="John", surname="Doe")

    def test_create_with_profile_missing_password(self, auth_service, test_client):
        with test_client.application.app_context():
            with pytest.raises(ValueError, match="Password is required."):
                auth_service.create_with_profile(email="test@example.com", name="John", surname="Doe")

    def test_create_with_profile_missing_name(self, auth_service):
        with pytest.raises(ValueError, match="Name is required."):
            auth_service.create_with_profile(email="test@example.com", password="pass", surname="Doe")

    def test_create_with_profile_missing_surname(self, auth_service, test_client):
        with test_client.application.app_context():
            with pytest.raises(ValueError, match="Surname is required."):
                auth_service.create_with_profile(email="test@example.com", password="pass", name="John")

    def test_create_with_profile_rollback_on_error(self, auth_service):
        user_data = {"email": "new@example.com", "password": "password123", "name": "John", "surname": "Doe"}

        with patch.object(auth_service, "create", side_effect=Exception("DB Error")):
            with patch.object(auth_service.repository.session, "rollback") as mock_rollback:
                with pytest.raises(Exception, match="DB Error"):
                    auth_service.create_with_profile(**user_data)

                mock_rollback.assert_called_once()
