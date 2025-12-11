from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService


class TestAuth2FAMethods:

    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_generate_key_qr_authenticated(self, auth_service):
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.profile.name = "John Doe"

        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.generate_key", return_value="test_2fa_key") as mock_generate_key:
                with patch("app.modules.auth.services.generate_qr", return_value="qr_code_image") as mock_generate_qr:
                    key, qr = auth_service.generate_key_qr()

                    assert key == "test_2fa_key"
                    assert qr == "qr_code_image"
                    mock_generate_key.assert_called_once()
                    mock_generate_qr.assert_called_once_with("test_2fa_key", "John Doe")

    def test_generate_key_qr_unauthenticated(self, auth_service):
        mock_user = Mock()
        mock_user.is_authenticated = False

        with patch("app.modules.auth.services.current_user", mock_user):
            result = auth_service.generate_key_qr()

            assert result is None

    def test_confirm_and_add_2fa_success(self, auth_service):
        mock_user = Mock()
        mock_user.is_authenticated = True
        auth_service.repository = Mock()
        auth_service.repository.update.return_value = Mock(twofa_key="encripted_key")
        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.verify", return_value=True) as mock_verify:
                result = auth_service.confirm_and_add_2fa("encrypted_key", "123456")

                assert result is True
                mock_verify.assert_called_once_with("encrypted_key", "123456")

    def test_confirm_and_add_2fa_invalid_code(self, auth_service):
        mock_user = Mock()
        mock_user.is_authenticated = True

        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.verify", return_value=False) as mock_verify:
                result = auth_service.confirm_and_add_2fa("encrypted_key", "wrong_code")

                assert result is False
                mock_verify.assert_called_once_with("encrypted_key", "wrong_code")

    def test_confirm_and_add_2fa_unauthenticated(self, auth_service):
        mock_user = Mock()
        mock_user.is_authenticated = False

        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.verify") as mock_verify:
                result = auth_service.confirm_and_add_2fa("encrypted_key", "123456")

                assert result is False
                mock_verify.assert_not_called()

    def test_confirm_and_add_2fa_not_persists_when_incorrect_code(self, auth_service):
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        auth_service.repository.update = Mock()
        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.verify", return_value=False):

                result = auth_service.confirm_and_add_2fa("encrypted_key", "123456")

                assert result is False
                auth_service.repository.update.assert_not_called()

    def test_validate_failing_anonymous_2fa_code(self, auth_service):
        mock_user = Mock()
        mock_user.is_anonymous = True
        email = "email@email.com"

        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.verify", return_value=False):

                result = auth_service.validate_2fa_code(123456, email)

                assert result is False

    def test_validate_success_anonymous_2fa_code(self, auth_service):
        mock_user = Mock()
        mock_user.is_anonymous = True
        email = "email@email.com"

        with patch("app.modules.auth.services.current_user", mock_user):
            with patch("app.modules.auth.services.verify", return_value=True):

                result = auth_service.validate_2fa_code(123456, email)

                assert result is True

    def test_check_2fa_is_enabled_true(self, auth_service):
        email = "email@email.com"
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.email = email
        mock_user.twofa_key = "Secret key"

        auth_service.repository = Mock()
        auth_service.repository.get_by_email.return_value = mock_user
        result = auth_service.check_2FA_is_enabled(email)
        assert result is True

    def test_check_2fa_is_enabled_false(self, auth_service):
        email = "email@email.com"
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.email = email
        mock_user.twofa_key = None

        auth_service.repository = Mock()
        auth_service.repository.get_by_email.return_value = mock_user
        result = auth_service.check_2FA_is_enabled(email)
        assert result is False
