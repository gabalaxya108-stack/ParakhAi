from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class StorageResult:
    storage_key: str
    file_path: str
    public_url: str
    file_size: int

class BaseStorageService(ABC):
    """
    Abstract storage service for persisting and retrieving inspection assets.
    Enables pluggable local filesystem, Azure Blob Storage, or AWS S3.
    """

    @abstractmethod
    def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        subfolder: str = ""
    ) -> StorageResult:
        """Saves file bytes and returns storage metadata."""
        pass

    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        """Returns the local or cached file path for processing."""
        pass

    @abstractmethod
    def get_public_url(self, storage_key: str) -> str:
        """Returns the public URL or relative endpoint to access the file."""
        pass
