from typing import Dict, Any
from pydantic import ValidationError
from backend.app.schemas.extraction import ExtractedFieldsContainer, REQUIRED_DECLARATION_FIELDS
from backend.app.core.errors import AppException

class ExtractionValidator:
    """
    Validates model output against strict declaration schemas.
    Rejects malformed outputs, missing fields, or hallucinated keys.
    """

    @staticmethod
    def validate_model_payload(payload: Dict[str, Any]) -> ExtractedFieldsContainer:
        if not isinstance(payload, dict):
            raise AppException(
                message="Model output must be a valid JSON dictionary.",
                error_code="MALFORMED_EXTRACTION_OUTPUT",
                status_code=422
            )

        # Check for unexpected/hallucinated fields
        extra_keys = set(payload.keys()) - set(REQUIRED_DECLARATION_FIELDS)
        if extra_keys:
            raise AppException(
                message=f"Model output contains unsupported or hallucinated fields: {sorted(list(extra_keys))}",
                error_code="UNSUPPORTED_EXTRACTION_FIELDS",
                status_code=422,
                details={"extra_keys": sorted(list(extra_keys))}
            )

        # Check for missing required field envelopes
        missing_keys = set(REQUIRED_DECLARATION_FIELDS) - set(payload.keys())
        if missing_keys:
            raise AppException(
                message=f"Model output is missing mandatory declaration envelopes: {sorted(list(missing_keys))}",
                error_code="MISSING_DECLARATION_ENVELOPES",
                status_code=422,
                details={"missing_keys": sorted(list(missing_keys))}
            )

        # Strict Pydantic parsing
        try:
            return ExtractedFieldsContainer(**payload)
        except ValidationError as e:
            raise AppException(
                message=f"Model output failed strict schema validation: {str(e)}",
                error_code="MALFORMED_EXTRACTION_OUTPUT",
                status_code=422,
                details=e.errors()
            )
