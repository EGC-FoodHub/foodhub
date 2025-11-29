import pytest
from unittest.mock import patch, Mock
import os
from app.modules.auth.services import AuthenticationService

class TestAuthInit:
    
    def test_init_sets_resend_api_key(self):
        """Test que __init__ configura correctamente la API key de Resend"""
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_api_key_123'}):
            with patch('app.modules.auth.services.resend') as mock_resend:
                service = AuthenticationService()
                
                assert service.RESEND_API_KEY == 'test_api_key_123'
                assert mock_resend.api_key == 'test_api_key_123'
    
    def test_init_initializes_repositories(self):
        """Test que __init__ inicializa los repositorios correctamente"""
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
            service = AuthenticationService()
            
            assert hasattr(service, 'repository')
            assert hasattr(service, 'user_profile_repository')
            assert service.repository is not None
            assert service.user_profile_repository is not None