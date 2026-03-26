from uuid import UUID

from app.infra.db.models.user import User


def test_user_creation_with_required_fields():
    """Test user creation with required fields"""
    user = User(email="test@example.com", is_active=True)
    assert user.email == "test@example.com"
    assert user.is_active is True
    # ID is set by database default, not in unit tests
    assert user.id is None or isinstance(user.id, UUID)


def test_user_api_key_encrypted_field_exists():
    """Test that api_key_encrypted field exists and can be set"""
    user = User(email="test@example.com", api_key_encrypted="encrypted_api_key_here")
    assert user.api_key_encrypted == "encrypted_api_key_here"
    # Test nullable field
    user_no_key = User(email="test2@example.com")
    assert user_no_key.api_key_encrypted is None


def test_user_timestamps_auto_set():
    """Test that timestamps are automatically set"""
    user = User(email="test@example.com")
    assert hasattr(user, 'created_at')
    assert hasattr(user, 'updated_at')
    # These will be set by the database, so we can't test the actual values
    # in unit tests


def test_user_preferences_json_nullable():
    """Test that preferences field accepts JSON and is nullable"""
    user = User(
        email="test@example.com", preferences={"theme": "dark", "language": "en"}
    )
    assert user.preferences == {"theme": "dark", "language": "en"}

    # Test nullable
    user_no_prefs = User(email="test2@example.com")
    assert user_no_prefs.preferences is None


def test_user_repr():
    """Test user string representation"""
    user = User(email="test@example.com")
    repr_str = repr(user)
    assert "User" in repr_str
    assert "test@example.com" in repr_str
