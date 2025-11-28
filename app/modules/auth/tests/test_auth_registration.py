import pytest
from unittest.mock import Mock, patch
from app.modules.auth.services import AuthenticationService

class TestAuthRegistration:
    
    @pytest.fixture
    def auth_service(self):
        return AuthenticationService()

    def test_is_email_available_true(self, auth_service):
        with patch.object(auth_service.repository, 'get_by_email', return_value=None):
            result = auth_service.is_email_available("new@example.com")
            assert result is True

    def test_is_email_available_false(self, auth_service):
        mock_user = Mock()
        with patch.object(auth_service.repository, 'get_by_email', return_value=mock_user):
            result = auth_service.is_email_available("existing@example.com")
            assert result is False

    def test_create_with_profile_success(self, auth_service):
        user_data = {
            "email": "new@example.com",
            "password": "password123",
            "name": "John",
            "surname": "Doe"
        }
        
        mock_user = Mock()
        mock_user.id = 1
        
        with patch.object(auth_service, 'create', return_value=mock_user):
            with patch.object(auth_service.user_profile_repository, 'create'):
                with patch('app.modules.auth.services.generate_verification_token', return_value="token123"):
                    with patch('app.modules.auth.services.send_email_verification'):
                        with patch.object(auth_service.repository.session, 'commit'):
                            result = auth_service.create_with_profile(**user_data)
                            assert result == mock_user

    def test_create_with_profile_missing_email(self, auth_service):
        with pytest.raises(ValueError, match="Email is required."):
            auth_service.create_with_profile(password="pass", name="John", surname="Doe")

    def test_create_with_profile_missing_password(self, auth_service):
        with pytest.raises(ValueError, match="Password is required."):
            auth_service.create_with_profile(email="test@example.com", name="John", surname="Doe")