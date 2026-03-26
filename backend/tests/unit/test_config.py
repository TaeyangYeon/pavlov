from app.core.config import get_settings


def test_settings_creation() -> None:
    """Test settings can be created."""
    # This test will need environment variables set
    # For now, it's a placeholder to ensure the config module works
    pass


def test_get_settings_cached() -> None:
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
