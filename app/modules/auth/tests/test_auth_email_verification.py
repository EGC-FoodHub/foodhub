from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService, EmailVerificationError


class TestAuthEmailVerification:

    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_verify_email_success(self, auth_service):
        mock_user = Mock()
        mock_user.is_email_verified = False
        mock_user.email_verification_token = "some_token"

        with patch("app.modules.auth.services.confirm_verification_token", return_value="test@example.com"):
            with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
                with patch.object(auth_service.repository.session, "commit"):
                    result = auth_service.verify_email("valid_token")

                    assert result == mock_user
                    assert mock_user.is_email_verified is True
                    assert mock_user.email_verification_token is None

    def test_verify_email_invalid_token(self, auth_service):
        with patch("app.modules.auth.services.confirm_verification_token", return_value=None):
            with pytest.raises(EmailVerificationError, match="Invalid or expired verification token."):
                auth_service.verify_email("invalid_token")

    def test_verify_email_user_not_found(self, auth_service):
        with patch("app.modules.auth.services.confirm_verification_token", return_value="test@example.com"):
            with patch.object(auth_service.repository, "get_by_email", return_value=None):
                with pytest.raises(EmailVerificationError, match="User not found for the given token."):
                    auth_service.verify_email("valid_token")

    def test_verify_email_already_verified(self, auth_service):
        mock_user = Mock()
        mock_user.is_email_verified = True

        with patch("app.modules.auth.services.confirm_verification_token", return_value="test@example.com"):
            with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
                with pytest.raises(EmailVerificationError, match="Email already verified."):
                    auth_service.verify_email("valid_token")
