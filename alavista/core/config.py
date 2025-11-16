"""
Configuration management for Alavista using Pydantic Settings.

This module provides the central configuration system that loads settings
from environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.

    All settings can be overridden via environment variables prefixed with nothing
    (direct match) or through a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: str = Field(default="dev", description="Environment (dev, prod, test)")

    # Application metadata
    app_name: str = Field(default="Alavista", description="Application name")

    # Logging configuration
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    json_logs: bool = Field(default=False, description="Enable JSON-formatted structured logging")

    # Data storage
    data_dir: Path = Field(
        default=Path("./data"), description="Directory for storing application data"
    )
    db_path: Path = Field(
        default=Path("./data/alavista.db"), description="SQLite database path"
    )

    # HTTP API configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

    # Ollama/LLM configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama service base URL"
    )
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama service URL")
    ollama_model: str = Field(
        default="llama3.1:8b", description="Default Ollama model for text generation"
    )
    llm_model_tier_default: str = Field(
        default="reasoning_default", description="Default LLM tier for reasoning"
    )

    # Embeddings configuration
    embedding_model_name: str = Field(
        default="all-minilm-l6-v2", description="Default embedding model name"
    )

    # Vector search configuration
    vector_backend: str = Field(
        default="faiss",
        description="Vector backend to use (faiss | memory)",
    )
    vector_index_dir: Path = Field(
        default=Path("./data/vector_index"), description="Directory for FAISS index files"
    )
    vector_normalize: bool = Field(
        default=True, description="Whether to L2-normalize embeddings before indexing/search"
    )

    # Persona configuration
    auto_create_persona_corpora: bool = Field(
        default=False, description="Automatically create persona manual corpora on startup"
    )

    def __init__(self, **kwargs):
        """Initialize settings and ensure data directory exists."""
        super().__init__(**kwargs)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_index_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance.

    This function uses lru_cache to ensure settings are loaded only once
    and reused throughout the application (singleton pattern).

    Returns:
        Settings: The application settings instance
    """
    return Settings()
