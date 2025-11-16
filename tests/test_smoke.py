"""
Smoke tests to verify basic imports and module structure.
"""

import pytest


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_alavista(self):
        """Test that main package can be imported."""
        import alavista
        assert hasattr(alavista, "__version__")
    
    def test_import_core(self):
        """Test that core module can be imported."""
        import alavista.core
        assert alavista.core is not None
    
    def test_import_config(self):
        """Test that config module can be imported."""
        from alavista.core.config import Settings, get_settings
        assert Settings is not None
        assert callable(get_settings)
    
    def test_import_logging(self):
        """Test that logging module can be imported."""
        from alavista.core.logging import configure_logging, get_logger
        assert callable(configure_logging)
        assert callable(get_logger)
    
    def test_import_container(self):
        """Test that container module can be imported."""
        from alavista.core.container import Container, get_container
        assert Container is not None
        assert callable(get_container)
    
    def test_import_interfaces(self):
        """Test that interfaces module can be imported."""
        import alavista.interfaces
        assert alavista.interfaces is not None
    
    def test_import_mcp(self):
        """Test that MCP module can be imported."""
        import alavista.mcp
        assert alavista.mcp is not None
    
    def test_import_api(self):
        """Test that API module can be imported."""
        import alavista.api
        assert alavista.api is not None
    
    def test_import_ingestion(self):
        """Test that ingestion module can be imported."""
        import alavista.ingestion
        assert alavista.ingestion is not None
    
    def test_import_search(self):
        """Test that search module can be imported."""
        import alavista.search
        assert alavista.search is not None
    
    def test_import_vector(self):
        """Test that vector module can be imported."""
        import alavista.vector
        assert alavista.vector is not None
    
    def test_import_graph(self):
        """Test that graph module can be imported."""
        import alavista.graph
        assert alavista.graph is not None
    
    def test_import_ontology(self):
        """Test that ontology module can be imported."""
        import alavista.ontology
        assert alavista.ontology is not None
    
    def test_import_personas(self):
        """Test that personas module can be imported."""
        import alavista.personas
        assert alavista.personas is not None


class TestBasicFunctionality:
    """Test basic functionality of core components."""
    
    def test_settings_creation(self):
        """Test that Settings can be instantiated."""
        from alavista.core.config import Settings
        settings = Settings()
        assert settings.app_name == "Alavista"
    
    def test_logger_creation(self):
        """Test that loggers can be created."""
        from alavista.core.logging import get_logger
        logger = get_logger("test")
        assert logger.name == "test"
    
    def test_container_access(self):
        """Test that container can be accessed."""
        from alavista.core.container import get_container
        container = get_container()
        assert container is not None
        
        # Test that we can get settings from container
        settings = container.get_settings()
        assert settings.app_name == "Alavista"
