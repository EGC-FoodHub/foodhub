import pytest
from unittest.mock import Mock, patch
import os
from app.modules.auth.services import AuthenticationService

class TestAuthPasswordRecovery:
    
    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_send_recover_email(self, auth_service):
        """Test envío de email de recuperación"""
        with patch('app.modules.auth.services.resend.Emails.send') as mock_send:
            with patch('app.modules.auth.services.secrets.token_hex', return_value="abc123"):
                # Limpiar variable de entorno si existe
                if "TOKEN_KEY" in os.environ:
                    del os.environ["TOKEN_KEY"]
                
                auth_service.send_recover_email("test@example.com")
                
                mock_send.assert_called_once()
                assert os.environ.get("TOKEN_KEY") == "abc123"
                
                # Verificar parámetros del email
                call_args = mock_send.call_args[0][0]
                assert call_args["to"] == ["test@example.com"]
                assert call_args["subject"] == "FoodHub password change"
                assert "abc123" in call_args["html"]

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
        
        with patch('app.modules.auth.services.db.session.commit') as mock_commit:
            auth_service.update_password(mock_user, "newpassword")
            
            mock_user.set_password.assert_called_once_with("newpassword")
            mock_commit.assert_called_once()