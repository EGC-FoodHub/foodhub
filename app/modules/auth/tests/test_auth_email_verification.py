from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService, EmailVerificationError
from app.modules.auth.utils.email_token import generate_verification_token


class TestAuthEmailVerification:

    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_verify_email_failure(self, auth_service):
        email = "test@example.com"
        token = generate_verification_token(email)

        mock_user = Mock()
        mock_user.is_email_verified = False
        mock_user.email_verification_token = token

        with patch.object(
            auth_service.repository,
            "get_by_email",
            return_value=mock_user,
        ):
            with patch.object(auth_service.repository.session, "commit") as mock_commit:

                result = auth_service.verify_email(token)

        assert result is mock_user
        assert mock_user.is_email_verified is True
        assert mock_user.email_verification_token is None
        mock_commit.assert_called_once()

    def test_verify_email_failure(self, auth_service):
        email = "test@example.com"
        token = generate_verification_token(email)

        mock_user = Mock()
        mock_user.is_email_verified = False
        mock_user.email_verification_token = token

        with patch.object(
            auth_service.repository,
            "get_by_email",
            return_value=mock_user,
        ):
            with patch.object(auth_service.repository.session, "commit") as mock_commit:
              with pytest.raises(EmailVerificationError):
                auth_service.verify_email("Not the correct token")

        assert mock_user.is_email_verified is False
        assert mock_user.email_verification_token is not None
        mock_commit.assert_not_called()

    def test_verify_email_double_verify_should_fail(self, auth_service):
      email = "test@example.com"
      token = generate_verification_token(email)

      mock_user = Mock()
      mock_user.is_email_verified = False
      mock_user.email_verification_token = token

      with patch.object(
          auth_service.repository,
          "get_by_email",
          return_value=mock_user,
      ):
          with patch.object(auth_service.repository.session, "commit") as mock_commit:

              result = auth_service.verify_email(token)

      assert result is mock_user
      assert mock_user.is_email_verified is True
      assert mock_user.email_verification_token is None
      mock_commit.assert_called_once()

      with patch.object(
            auth_service.repository,
            "get_by_email",
            return_value=mock_user,
        ):
            with patch.object(auth_service.repository.session, "commit") as mock_commit:
              with pytest.raises(EmailVerificationError):
                auth_service.verify_email(token)

      assert mock_user.is_email_verified is True
      assert mock_user.email_verification_token is None
      mock_commit.assert_not_called()


    def test_verify_email_no_user(self, auth_service):
      result = None
      with patch.object(
            auth_service.repository,
            "get_by_email",
            return_value=None,
        ):
            with patch.object(auth_service.repository.session, "commit") as mock_commit:
              with pytest.raises(EmailVerificationError):
                result = auth_service.verify_email("token")
      assert result is None
      mock_commit.assert_not_called()


    def test_register_then_login_fails_if_not_verified(self, auth_service):
      email = "new@example.com"
      password = "password123"

      created_user = Mock()
      created_user.email = email
      created_user.is_email_verified = False
      created_user.check_password.return_value = True

      with patch.object(auth_service, "create", return_value=created_user):
          with patch.object(auth_service.user_profile_repository, "create"):
              with patch("app.modules.auth.services.generate_verification_token", return_value="token123"):
                  with patch("app.modules.auth.services.send_email_verification"):
                      with patch.object(auth_service.repository.session, "commit"):

                          user = auth_service.create_with_profile(
                              email=email,
                              password=password,
                              name="John",
                              surname="Doe",
                          )

      assert user is created_user
      assert user.is_email_verified is False

      with patch.object(auth_service.repository, "get_by_email", return_value=user):
          with pytest.raises(Exception):
              auth_service.login(email, password)

    def test_register_verify_then_login_success(self, auth_service):
      email = "new@example.com"
      password = "password123"

      created_user = Mock()
      created_user.email = email
      created_user.is_email_verified = False
      created_user.check_password.return_value = True

      with patch.object(auth_service, "create", return_value=created_user):
          with patch.object(auth_service.user_profile_repository, "create"):
                with patch("app.modules.auth.services.send_email_verification"):
                    with patch.object(auth_service.repository.session, "commit"):
                        user = auth_service.create_with_profile(
                            email=email,
                            password=password,
                            name="John",
                            surname="Doe",
                        )

      assert user is created_user
      assert user.is_email_verified is False

      with patch.object(auth_service.repository, "get_by_email", return_value=user):
          with patch.object(auth_service.repository.session, "commit"):
              auth_service.verify_email(user.email_verification_token)

      assert user.is_email_verified is True
      assert user.email_verification_token is None

      with patch.object(auth_service.repository, "get_by_email", return_value=user):
          with patch("app.modules.auth.services.login_user") as mock_login:
              auth_service.login(email, password)
              mock_login.assert_called_once_with(user, remember=True)
