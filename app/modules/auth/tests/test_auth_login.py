from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService


class TestAuthLogin:

    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_login_success(self, auth_service):
        mock_user = Mock()
        mock_user.check_password.return_value = True
        mock_user.is_email_verified = True

        with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
            with patch("app.modules.auth.services.login_user") as mock_login:
                result = auth_service.login("test@example.com", "password")

                mock_login.assert_called_once_with(mock_user, remember=True)

    def test_login_user_not_found(self, auth_service):
        with pytest.raises(Exception,match="There is no user with that email"):
            with patch.object(auth_service.repository, "get_by_email", return_value=None):
                result = auth_service.login("nonexistent@example.com", "password")
                assert result is False

    def test_login_wrong_password(self, auth_service):
        mock_user = Mock()
        mock_user.check_password.return_value = False

        with pytest.raises(Exception, match="Password or email is incorrect"):
            with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
                auth_service.login("test@example.com", "wrong_password")


    def test_check_password_success(self, auth_service):
        mock_user = Mock()
        mock_user.check_password.return_value = True

        with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
            result = auth_service.check_password("test@example.com", "password")
            assert result is True

    def test_check_password_failure(self, auth_service):
        mock_user = Mock()
        mock_user.check_password.return_value = False

        with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
            result = auth_service.check_password("test@example.com", "wrong_password")
            assert result is False
