import os
import io
from typing import Tuple, Optional, Set
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.errors import AppException
from backend.app.core.logging import get_logger

logger = get_logger("services.file_validator")

# Register HEIF/HEIC/AVIF support via pillow-heif if available
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception as e:
    logger.debug(f"pillow_heif registration: {e}")

# Universal mapping of supported image MIME types and file extensions
SUPPORTED_IMAGE_FORMATS = {
    # JPEG / Standard Photographic
    "image/jpeg": [".jpg", ".jpeg", ".jpe", ".jfif"],
    "image/jpg": [".jpg", ".jpeg"],
    "image/pjpeg": [".jpg", ".jpeg"],

    # PNG / Lossless Graphics
    "image/png": [".png"],
    "image/x-png": [".png"],

    # WEBP / Modern Web Image
    "image/webp": [".webp"],

    # HEIC / HEIF (Apple iPhone & Modern Smartphones)
    "image/heic": [".heic"],
    "image/heif": [".heif", ".hif"],
    "image/heic-sequence": [".heic"],
    "image/heif-sequence": [".heif"],

    # AVIF / Next-Gen Image
    "image/avif": [".avif"],

    # TIFF / High-Resolution Flatbed Scans
    "image/tiff": [".tif", ".tiff"],
    "image/x-tiff": [".tif", ".tiff"],

    # BMP / Windows Bitmap
    "image/bmp": [".bmp", ".dib"],
    "image/x-bmp": [".bmp"],
    "image/x-ms-bmp": [".bmp"],

    # GIF / Compuserve Graphics
    "image/gif": [".gif"],

    # Netpbm Portable Pixel/Gray/Bitmap Formats
    "image/x-portable-pixmap": [".ppm"],
    "image/x-portable-graymap": [".pgm"],
    "image/x-portable-bitmap": [".pbm"],
    "image/x-portable-anymap": [".pnm", ".ppm", ".pgm", ".pbm"],

    # ICO / Icon
    "image/x-icon": [".ico"],
    "image/vnd.microsoft.icon": [".ico"],
    "image/ico": [".ico"],

    # JPEG 2000
    "image/jp2": [".jp2", ".j2k", ".jpf", ".jpx"],

    # Truevision TGA
    "image/x-tga": [".tga"],
    "image/tga": [".tga"],

    # Adobe Photoshop Document
    "image/vnd.adobe.photoshop": [".psd"],
    "image/x-photoshop": [".psd"]
}

# Compile flat set of allowed lowercase extensions
ALL_ALLOWED_EXTENSIONS: Set[str] = {
    ext for exts in SUPPORTED_IMAGE_FORMATS.values() for ext in exts
}

# Fast-path binary magic byte signatures
MAGIC_BYTES_MAP = [
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"II*\x00", "image/tiff", ".tiff"),
    (b"MM\x00*", "image/tiff", ".tiff"),
    (b"BM", "image/bmp", ".bmp"),
    (b"GIF87a", "image/gif", ".gif"),
    (b"GIF89a", "image/gif", ".gif"),
    (b"\x00\x00\x01\x00", "image/x-icon", ".ico"),
    (b"\x00\x00\x00\x0cjP  \r\n\x87\n", "image/jp2", ".jp2"),
    (b"\xffO\xffQ", "image/jp2", ".jp2"),
    (b"P1", "image/x-portable-bitmap", ".pbm"),
    (b"P2", "image/x-portable-graymap", ".pgm"),
    (b"P3", "image/x-portable-pixmap", ".ppm"),
    (b"P4", "image/x-portable-bitmap", ".pbm"),
    (b"P5", "image/x-portable-graymap", ".pgm"),
    (b"P6", "image/x-portable-pixmap", ".ppm"),
]

class FileValidationService:
    """
    Universal image validation service supporting all standard, modern, and industrial
    image formats (JPEG, PNG, WEBP, HEIC, HEIF, AVIF, TIFF, BMP, GIF, PPM, ICO, JP2, etc.)
    with size thresholding and binary signature validation.
    """

    @classmethod
    def detect_image_format(cls, file_bytes: bytes, filename: str = "") -> Tuple[Optional[str], Optional[str]]:
        """
        Detects image MIME type and file extension using both fast-path binary magic headers
        and deep Pillow format verification.
        Returns: (mime_type, extension) or (None, None) if not a valid image.
        """
        if len(file_bytes) < 4:
            return None, None

        # 1. Fast-path binary magic bytes
        for magic, mime, ext in MAGIC_BYTES_MAP:
            if file_bytes.startswith(magic):
                return mime, ext

        # 2. Check RIFF-WEBP container
        if len(file_bytes) >= 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
            return "image/webp", ".webp"

        # 3. Check ISO Base Media File Format box (HEIC, HEIF, AVIF)
        if len(file_bytes) >= 12 and file_bytes[4:8] == b"ftyp":
            brand = file_bytes[8:12].lower()
            if brand in (b"avif", b"avis"):
                return "image/avif", ".avif"
            if brand in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"mif1", b"msf1"):
                return "image/heic", ".heic"

        # 4. Universal Pillow verification fallback
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                fmt = (img.format or "JPEG").upper()
                mime = Image.MIME.get(fmt, f"image/{fmt.lower()}")
                # Match to canonical extension
                ext = f".{fmt.lower()}"
                if ext == ".jpeg":
                    ext = ".jpg"
                elif ext in (".tiff", ".tif"):
                    ext = ".tiff"
                elif ext in (".heif", ".heic"):
                    ext = ".heic"
                return mime, ext
        except Exception:
            return None, None

    @classmethod
    def validate_image_upload(cls, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[str, str]:
        """
        Validates the uploaded file for:
        1. Non-empty content
        2. Maximum file size threshold
        3. Valid image extension or content
        4. Matching binary signature / readable image structure

        Returns: (detected_mime_type, file_extension)
        Raises: AppException on validation failure
        """
        if not file_bytes or len(file_bytes) == 0:
            raise AppException(
                message="The uploaded file is empty. Please select a valid package image.",
                error_code="EMPTY_FILE",
                status_code=400
            )

        # 1. Size check
        if len(file_bytes) > settings.max_upload_size_bytes:
            raise AppException(
                message=f"File size ({len(file_bytes) / (1024 * 1024):.1f}MB) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                error_code="FILE_TOO_LARGE",
                status_code=413,
                details={"max_size_mb": settings.MAX_UPLOAD_SIZE_MB, "actual_size_bytes": len(file_bytes)}
            )

        # 2. Extension check
        ext = os.path.splitext(filename or "")[1].lower()

        # Reject explicitly non-image extensions (e.g. .txt, .pdf, .exe, .zip)
        non_image_extensions = {".txt", ".pdf", ".docx", ".xlsx", ".zip", ".tar", ".gz", ".exe", ".sh", ".py", ".html", ".js"}
        if ext in non_image_extensions or (ext and ext not in ALL_ALLOWED_EXTENSIONS):
            raise AppException(
                message=f"Unsupported file extension '{ext}'. The platform supports all standard image formats (JPEG, PNG, WEBP, HEIC, TIFF, BMP, GIF, AVIF, PPM, etc.).",
                error_code="UNSUPPORTED_FILE_TYPE",
                status_code=400,
                details={"allowed_extensions": sorted(list(ALL_ALLOWED_EXTENSIONS)[:10])}
            )

        # 3. Binary signature / content inspection
        detected_mime, canonical_ext = cls.detect_image_format(file_bytes, filename)
        if not detected_mime:
            raise AppException(
                message="File content signature does not match a recognized, readable image format.",
                error_code="INVALID_FILE_SIGNATURE",
                status_code=400
            )

        # Use canonical extension if input extension is empty or unusual
        resolved_ext = ext if (ext and ext in ALL_ALLOWED_EXTENSIONS) else (canonical_ext or ".jpg")

        return detected_mime, resolved_ext
