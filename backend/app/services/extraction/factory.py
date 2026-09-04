import os
from typing import Optional, Tuple, Dict
from backend.app.core.config import settings
from backend.app.schemas.ocr import OCRResult
from backend.app.schemas.extraction import ExtractedFieldsContainer, ReconciliationDetail
from backend.app.services.extraction.base import ExtractionProvider, VisionExtractionProvider
from backend.app.services.extraction.mock import MockExtractionProvider
from backend.app.services.extraction.groq_provider import GroqQwenVisionProvider
from backend.app.services.extraction.reconciliation import ExtractionReconciler
from backend.app.core.logging import get_logger

logger = get_logger("services.extraction.factory")

class ReconciledPipelineExtractionProvider(ExtractionProvider):
    """
    Composite Extraction Pipeline:
    1. Runs Tesseract OCR extraction (Secondary / Corroboration / Fallback).
    2. Runs Qwen Vision via Groq (Primary Extraction) on the packaging image.
    3. If Groq Vision fails or API key is absent, gracefully falls back to Tesseract OCR without crashing.
    4. Reconciles both observations, detecting agreements and flagging perception conflicts as NEEDS_REVIEW.
    """

    def __init__(self, vision_provider: Optional[ExtractionProvider] = None):
        self.tesseract_extractor = MockExtractionProvider()
        self.vision_extractor = vision_provider or GroqQwenVisionProvider()
        self.last_reconciliation_ledger: Dict[str, ReconciliationDetail] = {}
        self.last_vision_status: str = "active"
        self.last_vision_raw_output: Optional[Dict] = None

    async def extract(
        self,
        image_path: str,
        ocr_result: OCRResult,
        inspection_id: str = ""
    ) -> ExtractedFieldsContainer:
        # Step 1: Secondary OCR extraction via Tesseract
        t0_tess = self.tesseract_extractor
        tesseract_fields = await t0_tess.extract(image_path, ocr_result, inspection_id=inspection_id)

        # Step 2: Primary Vision extraction via Qwen Vision (Groq)
        qwen_fields = None
        has_groq_key = bool(
            os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY") or getattr(settings, "GROK_API_KEY", None) or getattr(settings, "GROQ_API_KEY", None)
        )

        if has_groq_key:
            try:
                logger.info(f"Executing Qwen Vision extraction via Groq for '{inspection_id}'")
                qwen_fields = await self.vision_extractor.extract(image_path, ocr_result, inspection_id=inspection_id)
                self.last_vision_status = "active"
                self.last_vision_raw_output = qwen_fields.model_dump()
            except Exception as e:
                logger.warning(
                    f"Groq Vision extraction failed for inspection '{inspection_id}', falling back to Tesseract: {e}"
                )
                self.last_vision_status = "fallback_tesseract"
                self.last_vision_raw_output = {"error": str(e)}
        else:
            logger.info(
                f"GROQ_API_KEY not configured for inspection '{inspection_id}'; using Tesseract extraction as fallback"
            )
            self.last_vision_status = "unavailable"
            self.last_vision_raw_output = {"status": "GROQ_API_KEY not set in environment"}

        # Step 3: Reconcile or Fallback
        if qwen_fields:
            reconciled_fields, reconciliation_ledger = ExtractionReconciler.reconcile(
                tesseract_fields=tesseract_fields,
                qwen_fields=qwen_fields
            )
            self.last_reconciliation_ledger = reconciliation_ledger
            return reconciled_fields
        else:
            # Fallback directly to Tesseract
            # Tag all candidates to Tesseract
            self.last_reconciliation_ledger = {
                field: ReconciliationDetail(
                    field=field,
                    candidates=[],
                    resolution="tesseract_fallback",
                    conflict_detected=False,
                    reconciliation_notes="Vision extraction unavailable; results derived from secondary Tesseract OCR."
                )
                for field in tesseract_fields.model_dump().keys()
            }
            return tesseract_fields

def get_extraction_provider(provider_name: str = None) -> ExtractionProvider:
    """
    Factory function returning the configured declaration extraction provider.
    Priority:
    1. Explicit provider_name argument
    2. EXTRACTION_PROVIDER environment variable
    3. settings.EXTRACTION_PROVIDER
    """
    name = (
        provider_name
        or os.getenv("EXTRACTION_PROVIDER")
        or getattr(settings, "EXTRACTION_PROVIDER", "groq")
    ).lower().strip()

    if name in ["groq", "qwen", "vision", "composite"]:
        return ReconciledPipelineExtractionProvider()
    elif name in ["mock", "heuristic", "offline", "tesseract_only"]:
        return MockExtractionProvider()
    elif name in ["openai", "azure_openai"]:
        from backend.app.services.extraction.openai_provider import OpenAIExtractionProvider
        return OpenAIExtractionProvider()
    else:
        logger.warning(f"Unknown extraction provider '{name}', defaulting to ReconciledPipelineExtractionProvider.")
        return ReconciledPipelineExtractionProvider()
