from backend.app.services.storage.base import BaseStorageService, StorageResult
from backend.app.services.storage.local import LocalStorageService

_storage_instance = None

def get_storage_service() -> BaseStorageService:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorageService()
    return _storage_instance
