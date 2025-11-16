"""
Pytest configuration and shared fixtures for Alavista tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from alavista.core.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """
    Provide test-specific settings with safe defaults.
    
    Returns:
        Settings: Test configuration instance
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings(
            app_name="Alavista Test",
            log_level="DEBUG",
            data_dir=Path(tmpdir) / "data",
            ollama_host="http://localhost:11434",
            ollama_model="llama3.1:8b",
            json_logs=False,
        )
        yield settings


@pytest.fixture
def tmp_data_dir() -> Generator[Path, None, None]:
    """
    Provide an isolated temporary directory for test data.
    
    The directory is automatically cleaned up after the test.
    
    Yields:
        Path: Temporary data directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        data_dir.mkdir(parents=True, exist_ok=True)
        yield data_dir


@pytest.fixture
def sample_text() -> str:
    """
    Provide sample text for testing document processing.
    
    Returns:
        str: Sample text content
    """
    return """
    This is a sample document for testing purposes.
    
    It contains multiple paragraphs with various content.
    The Alavista platform is designed for investigative analysis.
    
    Documents can contain entities like John Doe and Acme Corporation.
    They may reference events, locations, and relationships.
    """


@pytest.fixture
def sample_metadata() -> dict:
    """
    Provide sample document metadata for testing.
    
    Returns:
        dict: Sample metadata dictionary
    """
    return {
        "source_type": "text",
        "title": "Test Document",
        "author": "Test Author",
        "date": "2024-01-01",
    }
