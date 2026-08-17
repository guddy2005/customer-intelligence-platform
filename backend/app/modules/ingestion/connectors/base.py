import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger("connectors")


class ConnectorError(Exception):
    """Base exception for all connector operations."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConnectorConnectionError(ConnectorError):
    """Raised when connection to data source fails."""
    pass


class ConnectorFetchError(ConnectorError):
    """Raised when fetching data from source fails."""
    pass


class ConnectorDataError(ConnectorError):
    """Raised when incoming data format is invalid or cannot be parsed."""
    pass


class BaseConnector(ABC):
    """
    Abstract Base Connector defining the standard interface
    for extracting raw records from various data sources (CSV, API, DB, etc.).
    """

    def __init__(self, source_name: str = "GENERIC_SOURCE"):
        self.source_name = source_name
        self.is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establishes or verifies connection/accessibility to the data source.
        Returns True if successful, raises ConnectorConnectionError otherwise.
        """
        pass

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches raw records from data source.
        Returns a list of raw dictionaries.
        Raises ConnectorFetchError or ConnectorDataError on failure.
        """
        pass

    def close(self) -> None:
        """
        Optional teardown/cleanup method.
        """
        self.is_connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
