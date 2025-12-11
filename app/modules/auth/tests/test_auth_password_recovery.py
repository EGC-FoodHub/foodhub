import os

from unittest.mock import Mock, patch

import pytest

from app.modules.auth.services import AuthenticationService


class TestAuthPasswordRecovery:

    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_send_recover_email(self, auth_service):
        """Test envío de email de recuperación"""
        # Limpiar variable de entorno si existe
        
        mock_user = Mock()
        mock_user.email="test@example.com"

        with patch.dict(os.environ, {"TOKEN_KEY": ""}, clear=False):
            with patch.object(auth_service.repository, "get_by_email", return_value=mock_user):
                with patch("app.modules.auth.services.send_password_change_email") as mock_send:
                    # Parchar el token
                    with patch("app.modules.auth.services.secrets.token_hex", return_value="abc123"):

                        # Llamamos a la función real, NO parcheada
                        auth_service.send_recover_email(mock_user.email)

                        # Comprobaciones
                        mock_send.assert_called_once()

                        # Capturar argumentos de la llamada
                        args, kwargs = mock_send.call_args

                        user_arg = args[0]
                        token_arg = args[1]

                        assert user_arg.email == "test@example.com"
                        assert token_arg == "abc123"


    def test_validate_recovery_success(self, auth_service):
        """Test validación de recuperación exitosa"""
        os.environ["TOKEN_KEY"] = "abc123"

        result = auth_service.validate_recovery("abc123", "newpass", "newpass")
        assert result is True

    def test_validate_recovery_wrong_token(self, auth_service):
        """Test validación con token incorrecto"""
        os.environ["TOKEN_KEY"] = "abc123"

        result = auth_service.validate_recovery("wrongtoken", "newpass", "newpass")
        assert result is False

    def test_validate_recovery_password_mismatch(self, auth_service):
        os.environ["TOKEN_KEY"] = "abc123"

        result = auth_service.validate_recovery("abc123", "newpass", "different")
        assert result is False

    def test_validate_recovery_token_none(self, auth_service):
        os.environ["TOKEN_KEY"] = "abc123"

        result = auth_service.validate_recovery(None, "newpass", "newpass")
        assert result is False

    def test_update_password(self, auth_service):
        mock_user = Mock()

        with patch("app.modules.auth.services.db.session.commit") as mock_commit:
            auth_service.update_password(mock_user, "newpassword")

            mock_user.set_password.assert_called_once_with("newpassword")
            mock_commit.assert_called_once()
