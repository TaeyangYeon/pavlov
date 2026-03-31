from uuid import UUID
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.config import Settings
from app.domain.user.schemas import UserCreate, UserResponse, APIKeySetRequest, APIKeySetResponse
from app.domain.user.service import UserService
from app.domain.user.interfaces import UserRepositoryPort
from app.domain.user.exceptions import UserNotFoundError, InvalidAPIKeyError


class TestUserService:
    """Test suite for UserService (TDD Red phase)"""

    @pytest.fixture
    def mock_repository(self):
        """Mock UserRepositoryPort for testing"""
        repository = Mock(spec=UserRepositoryPort)
        return repository

    @pytest.fixture
    def mock_settings(self):
        """Mock Settings for testing"""
        settings = Mock(spec=Settings)
        settings.anthropic_api_key = "test-env-key"
        return settings

    @pytest.fixture
    def user_service(self, mock_repository, mock_settings):
        """UserService instance with mocked dependencies"""
        return UserService(
            repository=mock_repository,
            settings=mock_settings
        )

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID"""
        return UUID("12345678-1234-5678-9012-123456789012")

    @pytest.fixture
    def sample_user_create(self):
        """Sample user creation data"""
        return UserCreate(email="test@example.com")

    @pytest.fixture
    def sample_user_response(self, sample_user_id):
        """Sample user response"""
        from datetime import datetime
        return UserResponse(
            id=sample_user_id,
            email="test@example.com",
            has_api_key=False,
            is_active=True,
            created_at=datetime.now()
        )

    @pytest.fixture
    def sample_api_key_request(self):
        """Sample API key set request"""
        return APIKeySetRequest(api_key="sk-ant-api03-test")

    async def test_set_api_key_validates_before_storing(
        self, user_service, mock_repository, sample_user_id, sample_api_key_request
    ):
        """set_api_key should validate key before storing"""
        with patch.object(user_service, '_validate_anthropic_key') as mock_validate:
            mock_validate.side_effect = InvalidAPIKeyError("Key rejected")
            
            with pytest.raises(InvalidAPIKeyError):
                await user_service.set_api_key(sample_user_id, sample_api_key_request)
            
            # Verify repository.store_api_key was NOT called
            mock_repository.store_api_key.assert_not_called()

    async def test_set_api_key_stores_after_valid_key(
        self, user_service, mock_repository, sample_user_id, sample_api_key_request
    ):
        """set_api_key should store key after successful validation"""
        with patch.object(user_service, '_validate_anthropic_key') as mock_validate:
            mock_validate.return_value = None  # Validation passed
            mock_repository.store_api_key.return_value = None
            
            result = await user_service.set_api_key(sample_user_id, sample_api_key_request)
            
            # Verify repository.store_api_key was called once
            mock_repository.store_api_key.assert_called_once_with(
                sample_user_id, sample_api_key_request.api_key
            )

    async def test_set_api_key_returns_success_message(
        self, user_service, mock_repository, sample_user_id, sample_api_key_request
    ):
        """set_api_key should return success response after storing"""
        with patch.object(user_service, '_validate_anthropic_key') as mock_validate:
            mock_validate.return_value = None  # Validation passed
            mock_repository.store_api_key.return_value = None
            
            result = await user_service.set_api_key(sample_user_id, sample_api_key_request)
            
            assert isinstance(result, APIKeySetResponse)
            assert result.success is True
            assert "validated and stored securely" in result.message

    async def test_get_api_key_delegates_to_repository(
        self, user_service, mock_repository, sample_user_id
    ):
        """get_api_key should delegate to repository"""
        expected_key = "sk-ant-api03-decrypted"
        mock_repository.get_api_key.return_value = expected_key
        
        result = await user_service.get_api_key(sample_user_id)
        
        mock_repository.get_api_key.assert_called_once_with(sample_user_id)
        assert result == expected_key

    async def test_create_user_delegates_to_repository(
        self, user_service, mock_repository, sample_user_create, sample_user_response
    ):
        """create_user should delegate to repository"""
        mock_repository.create.return_value = sample_user_response
        
        result = await user_service.create_user(sample_user_create)
        
        mock_repository.create.assert_called_once_with(sample_user_create)
        assert result == sample_user_response

    async def test_get_user_delegates_to_repository(
        self, user_service, mock_repository, sample_user_id, sample_user_response
    ):
        """get_user should delegate to repository when user exists"""
        mock_repository.get_by_id.return_value = sample_user_response
        
        result = await user_service.get_user(sample_user_id)
        
        mock_repository.get_by_id.assert_called_once_with(sample_user_id)
        assert result == sample_user_response

    async def test_get_user_raises_when_not_found(
        self, user_service, mock_repository, sample_user_id
    ):
        """get_user should raise UserNotFoundError when user doesn't exist"""
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(UserNotFoundError):
            await user_service.get_user(sample_user_id)

    async def test_validate_api_key_calls_anthropic(
        self, user_service, sample_api_key_request
    ):
        """_validate_anthropic_key should test key with AnthropicClient"""
        with patch('app.domain.user.service.AnthropicClient') as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = AsyncMock()
            mock_client_class.return_value = mock_client
            
            await user_service._validate_anthropic_key(sample_api_key_request.api_key)
            
            # Verify AnthropicClient was created with test key
            mock_client_class.assert_called_once_with(api_key=sample_api_key_request.api_key)
            # Verify test call was made
            mock_client.call.assert_called_once()

    async def test_validate_api_key_rejects_invalid(
        self, user_service, sample_api_key_request
    ):
        """_validate_anthropic_key should raise InvalidAPIKeyError on auth error"""
        with patch('app.domain.user.service.AnthropicClient') as mock_client_class:
            mock_client = Mock()
            mock_client.call.side_effect = Exception("Authentication failed")
            mock_client_class.return_value = mock_client
            
            with pytest.raises(InvalidAPIKeyError):
                await user_service._validate_anthropic_key(sample_api_key_request.api_key)

    async def test_validate_api_key_accepts_network_errors(
        self, user_service, sample_api_key_request
    ):
        """_validate_anthropic_key should accept keys that fail due to network errors"""
        with patch('app.domain.user.service.AnthropicClient') as mock_client_class:
            mock_client = Mock()
            mock_client.call.side_effect = Exception("Connection timeout")
            mock_client_class.return_value = mock_client
            
            # Should not raise (network errors are accepted)
            await user_service._validate_anthropic_key(sample_api_key_request.api_key)