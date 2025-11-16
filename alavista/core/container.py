"""
Dependency injection container for Alavista.

Provides factory functions for creating and managing core services.
Uses simple factory pattern with optional singleton behavior for stateful services.
"""

from functools import lru_cache

from alavista.core.config import Settings, get_settings
from alavista.core.corpus_store import SQLiteCorpusStore
from alavista.core.ingestion_service import IngestionService
from alavista.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class Container:
    """
    Simple dependency injection container.

    This container provides factory methods for core services.
    For stateful services (like Settings), it ensures singleton behavior.
    For stateless services, it can create new instances.

    Extension Pattern:
    ------------------
    To add a new service:

    1. Add a factory method to this class:
       ```python
       @staticmethod
       def create_my_service(settings: Optional[Settings] = None) -> MyService:
           settings = settings or get_settings()
           return MyService(settings)
       ```

    2. For singletons, use @lru_cache:
       ```python
       @staticmethod
       @lru_cache
       def get_my_service() -> MyService:
           return Container.create_my_service()
       ```

    3. Use in application code:
       ```python
       from alavista.core.container import Container
       my_service = Container.get_my_service()
       ```
    """

    @staticmethod
    @lru_cache
    def get_settings() -> Settings:
        """
        Get application settings (singleton).

        Returns:
            Settings: Application settings instance
        """
        return get_settings()

    @staticmethod
    def create_settings(**overrides) -> Settings:
        """
        Create a new Settings instance with optional overrides.

        Useful for testing with custom configuration.

        Args:
            **overrides: Setting overrides as keyword arguments

        Returns:
            Settings: New settings instance
        """
        return Settings(**overrides)

    @staticmethod
    def create_corpus_store(settings: Settings | None = None) -> SQLiteCorpusStore:
        """
        Create a CorpusStore instance.

        Args:
            settings: Settings instance (uses singleton if not provided)

        Returns:
            SQLiteCorpusStore: Corpus store instance
        """
        settings = settings or Container.get_settings()
        db_path = settings.data_dir / "corpus.db"
        return SQLiteCorpusStore(db_path)

    @staticmethod
    @lru_cache
    def get_corpus_store() -> SQLiteCorpusStore:
        """
        Get singleton CorpusStore instance.

        Returns:
            SQLiteCorpusStore: Corpus store singleton
        """
        return Container.create_corpus_store()

    @staticmethod
    def create_ingestion_service(
        corpus_store: SQLiteCorpusStore | None = None,
        min_chunk_size: int = 500,
        max_chunk_size: int = 1500,
    ) -> IngestionService:
        """
        Create an IngestionService instance.

        Args:
            corpus_store: Corpus store instance (uses singleton if not provided)
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters

        Returns:
            IngestionService: Ingestion service instance
        """
        corpus_store = corpus_store or Container.get_corpus_store()
        return IngestionService(
            corpus_store=corpus_store,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
        )

    @staticmethod
    @lru_cache
    def get_ingestion_service() -> IngestionService:
        """
        Get singleton IngestionService instance.

        Returns:
            IngestionService: Ingestion service singleton
        """
        return Container.create_ingestion_service()


def get_container() -> Container:
    """
    Get the dependency injection container.

    Returns:
        Container: The DI container instance
    """
    return Container()


# Example usage documentation
__doc__ += """

Usage Examples
--------------

Basic usage:
    >>> from alavista.core.container import Container
    >>> settings = Container.get_settings()
    >>> print(settings.app_name)
    'Alavista'

Custom settings for testing:
    >>> test_settings = Container.create_settings(
    ...     app_name="Test App",
    ...     log_level="DEBUG"
    ... )
    >>> print(test_settings.app_name)
    'Test App'

Extending with new services:
    >>> # In your service module:
    >>> class MyService:
    ...     def __init__(self, settings: Settings):
    ...         self.settings = settings
    ...
    >>> # In container.py:
    >>> # @staticmethod
    >>> # def create_my_service(settings=None):
    >>> #     return MyService(settings or Container.get_settings())
"""
