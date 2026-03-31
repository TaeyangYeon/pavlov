from uuid import UUID
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.user.schemas import UserCreate, UserResponse
from app.infra.crypto.encryption import EncryptionService
from app.infra.db.repositories.user_repository import UserRepository
from app.infra.db.models.user import User


class TestUserRepository:
    """Test suite for UserRepository (TDD Red phase)"""

    @pytest.fixture
    def mock_session(self):
        """Mock AsyncSession for testing"""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_encryption(self):
        """Mock EncryptionService for testing"""
        encryption = Mock(spec=EncryptionService)
        encryption.encrypt.return_value = "encrypted_value"
        encryption.decrypt.return_value = "plaintext_key"
        return encryption

    @pytest.fixture
    def user_repository(self, mock_session, mock_encryption):
        """UserRepository instance with mocked dependencies"""
        return UserRepository(
            session=mock_session,
            encryption=mock_encryption
        )

    @pytest.fixture
    def sample_user_data(self):
        """Sample user creation data"""
        return UserCreate(email="test@example.com")

    @pytest.fixture
    def sample_user_model(self):
        """Sample User model instance"""
        user_id = UUID("12345678-1234-5678-9012-123456789012")
        user = User(
            id=user_id,
            email="test@example.com",
            api_key_encrypted="encrypted_key",
            is_active=True
        )
        # Mock the created_at attribute
        from datetime import datetime
        user.created_at = datetime.now()
        return user

    async def test_store_api_key_encrypts_before_saving(
        self, user_repository, mock_session, mock_encryption
    ):
        """store_api_key should encrypt plaintext before saving to DB"""
        user_id = UUID("12345678-1234-5678-9012-123456789012")
        plaintext_key = "sk-ant-api03-plaintext"
        
        await user_repository.store_api_key(user_id, plaintext_key)
        
        # Verify encryption was called with plaintext
        mock_encryption.encrypt.assert_called_once_with(plaintext_key)
        
        # Verify session.execute was called (for UPDATE statement)
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_get_api_key_decrypts_on_retrieval(
        self, user_repository, mock_session, mock_encryption
    ):
        """get_api_key should decrypt stored value and return plaintext"""
        user_id = UUID("12345678-1234-5678-9012-123456789012")
        
        # Mock session returning encrypted value
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = "encrypted_value"
        mock_session.execute.return_value = mock_result
        
        result = await user_repository.get_api_key(user_id)
        
        # Verify decryption was called
        mock_encryption.decrypt.assert_called_once_with("encrypted_value")
        
        # Verify plaintext returned
        assert result == "plaintext_key"

    async def test_get_api_key_returns_none_when_not_set(
        self, user_repository, mock_session, mock_encryption
    ):
        """get_api_key should return None when user has no api_key_encrypted"""
        user_id = UUID("12345678-1234-5678-9012-123456789012")
        
        # Mock session returning None (no encrypted key)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await user_repository.get_api_key(user_id)
        
        # Verify None returned and decrypt not called
        assert result is None
        mock_encryption.decrypt.assert_not_called()

    async def test_create_user_returns_user_response(
        self, user_repository, mock_session, sample_user_data, sample_user_model
    ):
        """create should return UserResponse with id and email"""
        # Mock session operations
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Mock the created user (simulate DB assignment of ID)
        def mock_refresh(user):
            user.id = sample_user_model.id
            user.created_at = sample_user_model.created_at
            user.api_key_encrypted = None
            user.is_active = True
        mock_session.refresh.side_effect = mock_refresh
        
        result = await user_repository.create(sample_user_data)
        
        # Verify UserResponse structure
        assert isinstance(result, UserResponse)
        assert result.id == sample_user_model.id
        assert result.email == sample_user_data.email
        assert result.has_api_key is False  # no key set
        assert result.is_active is True

    async def test_get_by_id_returns_user_response(
        self, user_repository, mock_session, sample_user_model
    ):
        """get_by_id should return UserResponse when user exists"""
        user_id = sample_user_model.id
        
        # Mock session returning user
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        result = await user_repository.get_by_id(user_id)
        
        assert isinstance(result, UserResponse)
        assert result.id == user_id
        assert result.email == sample_user_model.email
        assert result.has_api_key is True  # user has encrypted key
        assert result.is_active is True

    async def test_get_by_id_returns_none_when_not_found(
        self, user_repository, mock_session
    ):
        """get_by_id should return None when user doesn't exist"""
        user_id = UUID("12345678-1234-5678-9012-123456789012")
        
        # Mock session returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await user_repository.get_by_id(user_id)
        
        assert result is None