from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService


class TestAuthProfileManagement:

    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_update_profile_success(self, auth_service):
        """Test actualización de perfil exitosa"""
        mock_form = Mock()
        mock_form.validate.return_value = True
        mock_form.data = {"name": "John", "surname": "Smith"}

        mock_updated_instance = Mock()

        with patch.object(auth_service, "update", return_value=mock_updated_instance):
            result, errors = auth_service.update_profile(1, mock_form)

            assert result == mock_updated_instance
            assert errors is None
            auth_service.update.assert_called_once_with(1, name="John", surname="Smith")

    def test_update_profile_validation_failed(self, auth_service):
        """Test actualización de perfil con validación fallida"""
        mock_form = Mock()
        mock_form.validate.return_value = False
        mock_form.errors = {"name": ["Name is required"]}

        result, errors = auth_service.update_profile(1, mock_form)

        assert result is None
        assert errors == {"name": ["Name is required"]}

    def test_get_user_by_email_existing(self, auth_service):
        """Test get_user_by_email con usuario existente"""
        mock_user = Mock()

        with patch.object(auth_service, "is_email_available", return_value=False):
            with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
                result = auth_service.get_user_by_email("existing@example.com")

                assert result == mock_user
                auth_service.repository.get_by_email.assert_called_once_with("existing@example.com")

    def test_get_user_by_email_nonexistent(self, auth_service):
        """Test get_user_by_email con usuario no existente"""
        with patch.object(auth_service, "is_email_available", return_value=True):
            result = auth_service.get_user_by_email("nonexistent@example.com")

            assert result is None

    def test_get_user_by_email_prints_email(self, auth_service, capsys):
        """Test que get_user_by_email imprime el email"""
        with patch.object(auth_service, "is_email_available", return_value=False):
            with patch.object(auth_service.repository, "get_by_email", return_value=Mock()):
                auth_service.get_user_by_email("test@example.com")

                captured = capsys.readouterr()
                assert "test@example.com" in captured.out
