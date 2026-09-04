import os
import re
from backend.app.core.config import settings
from backend.app.services.storage.base import BaseStorageService, StorageResult

class LocalStorageService(BaseStorageService):
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        # Keep only alphanumeric, dashes, underscores, and dots
        clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
        return clean or "uploaded_image"

    def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        subfolder: str = ""
    ) -> StorageResult:
        sanitized_name = self._sanitize_filename(filename)
        
        target_dir = os.path.join(self.upload_dir, subfolder) if subfolder else self.upload_dir
        os.makedirs(target_dir, exist_ok=True)

        destination_path = os.path.join(target_dir, sanitized_name)
        with open(destination_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        storage_key = os.path.join(subfolder, sanitized_name).replace("\\", "/") if subfolder else sanitized_name
        public_url = f"/uploads/{storage_key}"

        return StorageResult(
            storage_key=storage_key,
            file_path=destination_path,
            public_url=public_url,
            file_size=file_size
        )

    def get_file_path(self, storage_key: str) -> str:
        return os.path.join(self.upload_dir, storage_key)

    def get_public_url(self, storage_key: str) -> str:
        return f"/uploads/{storage_key}"
