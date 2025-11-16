"""
Tests for configuration management.
"""

import tempfile
from pathlib import Path

from alavista.core.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings class."""

    def test_default_values(self):
        """Test that settings have correct default values."""
        settings = Settings()

        assert settings.app_name == "Alavista"
        assert settings.log_level == "INFO"
        assert settings.data_dir == Path("./data")
        assert settings.ollama_host == "http://localhost:11434"
        assert settings.ollama_model == "llama3.1:8b"
        assert settings.json_logs is False

    def test_custom_values(self):
        """Test that settings can be overridden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(
                app_name="Test App",
                log_level="DEBUG",
                data_dir=Path(tmpdir) / "custom_data",
                ollama_host="http://test:11434",
                ollama_model="test-model",
                json_logs=True,
            )

            assert settings.app_name == "Test App"
            assert settings.log_level == "DEBUG"
            assert settings.data_dir == Path(tmpdir) / "custom_data"
            assert settings.ollama_host == "http://test:11434"
            assert settings.ollama_model == "test-model"
            assert settings.json_logs is True

    def test_environment_variables(self, monkeypatch):
        """Test that settings load from environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("APP_NAME", "Env App")
            monkeypatch.setenv("LOG_LEVEL", "ERROR")
            monkeypatch.setenv("DATA_DIR", tmpdir)
            monkeypatch.setenv("OLLAMA_HOST", "http://env:11434")
            monkeypatch.setenv("OLLAMA_MODEL", "env-model")

            settings = Settings()

            assert settings.app_name == "Env App"
            assert settings.log_level == "ERROR"
            assert settings.data_dir == Path(tmpdir)
            assert settings.ollama_host == "http://env:11434"
            assert settings.ollama_model == "env-model"

    def test_data_dir_creation(self):
        """Test that data directory is created on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "new_data_dir"
            assert not data_path.exists()

            Settings(data_dir=data_path)

            assert data_path.exists()
            assert data_path.is_dir()

    def test_case_insensitive_env_vars(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("app_name", "Lower Case App")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")

        settings = Settings()

        assert settings.app_name == "Lower Case App"
        assert settings.log_level == "WARNING"


class TestGetSettings:
    """Test suite for get_settings function."""

    def test_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_are_cached(self):
        """Test that settings are cached and reused."""
        # Clear the cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # They should be the exact same object
        assert id(settings1) == id(settings2)


class TestSettingsValidation:
    """Test suite for settings validation."""

    def test_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        settings = Settings(data_dir="./test_path")

        assert isinstance(settings.data_dir, Path)
        assert settings.data_dir == Path("./test_path")

    def test_bool_conversion(self, monkeypatch):
        """Test that boolean environment variables are properly converted."""
        monkeypatch.setenv("JSON_LOGS", "true")
        settings = Settings()
        assert settings.json_logs is True

        monkeypatch.setenv("JSON_LOGS", "false")
        get_settings.cache_clear()
        settings = Settings()
        assert settings.json_logs is False
