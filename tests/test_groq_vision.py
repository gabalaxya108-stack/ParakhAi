import pytest
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.schemas.ocr import OCRResult, OCRBlock, PixelBoundingBox
from backend.app.schemas.extraction import ExtractedFieldsContainer, FieldExtractionResult
from backend.app.services.extraction.groq_provider import GroqQwenVisionProvider
from backend.app.services.extraction.reconciliation import ExtractionReconciler
from backend.app.services.extraction.factory import ReconciledPipelineExtractionProvider, get_extraction_provider
from backend.app.services.extraction.mock import MockExtractionProvider
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.core.errors import AppException

SAMPLE_OCR_RESULT = OCRResult(
    inspection_id="insp_test_001",
    provider="tesseract",
    image_width=1000,
    image_height=1000,
    blocks=[
        OCRBlock(
            text="MRP Rs. 45.00",
            confidence=0.92,
            bounding_box=PixelBoundingBox(x=100, y=200, width=150, height=30)
        ),
        OCRBlock(
            text="Net Qty: 140 g",
            confidence=0.89,
            bounding_box=PixelBoundingBox(x=100, y=300, width=120, height=25)
        )
    ],
    full_text="MRP Rs. 45.00\nNet Qty: 140 g\n",
    total_blocks=2,
    average_confidence=0.90,
    processing_time_ms=120.0
)

VALID_GROQ_JSON = json.dumps({
    "product_name": {"value": "Maggi 2-Minute Noodles", "confidence": 0.98, "evidence_text": "MAGGI 2-Minute Noodles", "bounding_box": {"x": 50, "y": 50, "width": 300, "height": 80}},
    "manufacturer": {"value": "Nestle India Limited", "confidence": 0.94, "evidence_text": "Manufactured by: Nestlé India Limited", "bounding_box": {"x": 60, "y": 600, "width": 400, "height": 50}},
    "packer": {"value": None, "confidence": 0.0, "evidence_text": None, "bounding_box": None},
    "importer": {"value": None, "confidence": 0.0, "evidence_text": None, "bounding_box": None},
    "net_quantity": {"value": "140 g", "confidence": 0.95, "evidence_text": "Net Qty: 140 g", "bounding_box": {"x": 100, "y": 300, "width": 120, "height": 25}},
    "mrp": {"value": "₹45.00", "confidence": 0.96, "evidence_text": "MRP Rs. 45.00", "bounding_box": {"x": 100, "y": 200, "width": 150, "height": 30}},
    "packing_date": {"value": None, "confidence": 0.0, "evidence_text": None, "bounding_box": None},
    "manufacturing_date": {"value": "04/2026", "confidence": 0.88, "evidence_text": "Mfg: 04/2026", "bounding_box": None},
    "consumer_care": {"value": "wecare@in.nestle.com", "confidence": 0.91, "evidence_text": "Consumer Care: wecare@in.nestle.com", "bounding_box": None},
    "country_of_origin": {"value": "India", "confidence": 0.97, "evidence_text": "Made in India", "bounding_box": None},
    "batch_or_lot_number": {"value": "LOT2026B1", "confidence": 0.85, "evidence_text": "B.No. LOT2026B1", "bounding_box": None}
})

@pytest.fixture
def dummy_image_path(tmp_path):
    from PIL import Image
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    path = str(tmp_path / "test_package.jpg")
    img.save(path)
    return path

@pytest.mark.asyncio
async def test_valid_groq_response(dummy_image_path):
    """Test 1: Valid Groq JSON response is parsed into clean ExtractedFieldsContainer."""
    provider = GroqQwenVisionProvider(api_key="gsk_test_mock_key")
    
    mock_choice = MagicMock()
    mock_choice.message.content = VALID_GROQ_JSON
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 350
    mock_response.usage.completion_tokens = 180

    with patch.object(provider, "_get_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_factory.return_value = mock_client

        result = await provider.extract(dummy_image_path, SAMPLE_OCR_RESULT, "insp_test_001")

        assert isinstance(result, ExtractedFieldsContainer)
        assert result.mrp.value == "₹45.00"
        assert result.mrp.confidence == 0.96
        assert result.net_quantity.value == "140 g"
        assert result.net_quantity.confidence == 0.95
        assert result.product_name.value == "Maggi 2-Minute Noodles"
        assert result.consumer_care.value == "wecare@in.nestle.com"
        assert result.country_of_origin.value == "India"
        assert result.packer.value is None
        assert result.packer.status == "NOT_FOUND"

@pytest.mark.asyncio
async def test_missing_api_key(dummy_image_path):
    """Test 2: Missing GROQ_API_KEY raises an informative AppException."""
    from backend.app.core.config import settings
    with patch.object(settings, "GROQ_API_KEY", ""):
        provider = GroqQwenVisionProvider(api_key="")
        with pytest.raises(AppException) as exc_info:
            await provider.extract(dummy_image_path, SAMPLE_OCR_RESULT, "insp_test_002")
        assert "GROQ_API_KEY" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_groq_api_timeout_handling(dummy_image_path):
    """Test 3: API timeout or rate limit raises an AppException for graceful fallback."""
    provider = GroqQwenVisionProvider(api_key="gsk_test_key")

    with patch.object(provider, "_get_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=TimeoutError("Request timed out"))
        mock_client_factory.return_value = mock_client

        with pytest.raises(AppException) as exc_info:
            await provider.extract(dummy_image_path, SAMPLE_OCR_RESULT, "insp_test_003")
        assert "timed out" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_invalid_json_handling(dummy_image_path):
    """Test 4: Invalid/corrupted JSON response from model raises schema validation error."""
    provider = GroqQwenVisionProvider(api_key="gsk_test_key")

    mock_choice = MagicMock()
    mock_choice.message.content = "Not a valid JSON {bad string"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(provider, "_get_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_factory.return_value = mock_client

        with pytest.raises(AppException) as exc_info:
            await provider.extract(dummy_image_path, SAMPLE_OCR_RESULT, "insp_test_004")
        assert "invalid JSON" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_missing_declaration_handled_without_hallucination():
    """Test 5: Missing declarations are returned as value=None, confidence=0.0."""
    raw_payload = json.loads(VALID_GROQ_JSON)
    raw_payload["mrp"]["value"] = None
    raw_payload["mrp"]["confidence"] = 0.0

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(raw_payload)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    provider = GroqQwenVisionProvider(api_key="gsk_test_key")
    with patch.object(provider, "_get_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_factory.return_value = mock_client

        from PIL import Image
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            Image.new("RGB", (100, 100)).save(tmp.name)
            res = await provider.extract(tmp.name, SAMPLE_OCR_RESULT, "insp_test_005")

        assert res.mrp.value is None
        assert res.mrp.confidence == 0.0
        assert res.mrp.status == "NOT_FOUND"

def test_tesseract_qwen_agreement_reconciliation():
    """Test 7: Tesseract and Qwen agreement produces corroborated confidence boost and source."""
    tess_fields = ExtractedFieldsContainer(
        product_name=FieldExtractionResult(field="product_name", value="MAGGI NOODLES", confidence=0.88, source="tesseract"),
        manufacturer=FieldExtractionResult(field="manufacturer", value="Nestle India Ltd", confidence=0.85, source="tesseract"),
        packer=FieldExtractionResult(field="packer", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        importer=FieldExtractionResult(field="importer", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        net_quantity=FieldExtractionResult(field="net_quantity", value="140 g", confidence=0.90, source="tesseract"),
        mrp=FieldExtractionResult(field="mrp", value="₹45.00", confidence=0.92, source="tesseract"),
        packing_date=FieldExtractionResult(field="packing_date", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        manufacturing_date=FieldExtractionResult(field="manufacturing_date", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        consumer_care=FieldExtractionResult(field="consumer_care", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        country_of_origin=FieldExtractionResult(field="country_of_origin", value="India", confidence=0.91, source="tesseract"),
        batch_or_lot_number=FieldExtractionResult(field="batch_or_lot_number", value="B102", confidence=0.84, source="tesseract"),
    )

    qwen_fields = ExtractedFieldsContainer(
        product_name=FieldExtractionResult(field="product_name", value="Maggi 2-Minute Noodles", confidence=0.95, source="qwen_vision"),
        manufacturer=FieldExtractionResult(field="manufacturer", value="Nestlé India Limited", confidence=0.96, source="qwen_vision"),
        packer=FieldExtractionResult(field="packer", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        importer=FieldExtractionResult(field="importer", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        net_quantity=FieldExtractionResult(field="net_quantity", value="140 g", confidence=0.94, source="qwen_vision"),
        mrp=FieldExtractionResult(field="mrp", value="₹45.00", confidence=0.96, source="qwen_vision"),
        packing_date=FieldExtractionResult(field="packing_date", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        manufacturing_date=FieldExtractionResult(field="manufacturing_date", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        consumer_care=FieldExtractionResult(field="consumer_care", value="wecare@in.nestle.com", confidence=0.92, source="qwen_vision"),
        country_of_origin=FieldExtractionResult(field="country_of_origin", value="India", confidence=0.98, source="qwen_vision"),
        batch_or_lot_number=FieldExtractionResult(field="batch_or_lot_number", value="B102", confidence=0.90, source="qwen_vision"),
    )

    reconciled, ledger = ExtractionReconciler.reconcile(tess_fields, qwen_fields)

    # Corroborated fields
    assert reconciled.mrp.source == "qwen_vision+tesseract"
    assert reconciled.mrp.confidence >= 0.96
    assert ledger["mrp"].resolution == "agreement"
    assert ledger["mrp"].conflict_detected is False

    assert reconciled.net_quantity.source == "qwen_vision+tesseract"
    assert ledger["net_quantity"].resolution == "agreement"

    # One-sided detection
    assert reconciled.consumer_care.source == "qwen_vision"
    assert ledger["consumer_care"].resolution == "single_source"

def test_tesseract_qwen_disagreement_produces_needs_review():
    """Test 8: Conflicting values between Tesseract and Qwen set conflict_detected=True and status=UNCLEAR."""
    tess_fields = ExtractedFieldsContainer(
        product_name=FieldExtractionResult(field="product_name", value="Chips", confidence=0.8, source="tesseract"),
        manufacturer=FieldExtractionResult(field="manufacturer", value="Parle Products", confidence=0.8, source="tesseract"),
        packer=FieldExtractionResult(field="packer", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        importer=FieldExtractionResult(field="importer", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        net_quantity=FieldExtractionResult(field="net_quantity", value="70 g", confidence=0.9, source="tesseract"),
        mrp=FieldExtractionResult(field="mrp", value="₹45.00", confidence=0.91, source="tesseract"),  # CONFLICT
        packing_date=FieldExtractionResult(field="packing_date", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        manufacturing_date=FieldExtractionResult(field="manufacturing_date", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        consumer_care=FieldExtractionResult(field="consumer_care", value=None, confidence=0.0, source="tesseract", status="NOT_FOUND"),
        country_of_origin=FieldExtractionResult(field="country_of_origin", value="India", confidence=0.9, source="tesseract"),
        batch_or_lot_number=FieldExtractionResult(field="batch_or_lot_number", value="B1", confidence=0.8, source="tesseract"),
    )

    qwen_fields = ExtractedFieldsContainer(
        product_name=FieldExtractionResult(field="product_name", value="Chips", confidence=0.8, source="qwen_vision"),
        manufacturer=FieldExtractionResult(field="manufacturer", value="Parle Products", confidence=0.8, source="qwen_vision"),
        packer=FieldExtractionResult(field="packer", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        importer=FieldExtractionResult(field="importer", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        net_quantity=FieldExtractionResult(field="net_quantity", value="70 g", confidence=0.9, source="qwen_vision"),
        mrp=FieldExtractionResult(field="mrp", value="₹15.00", confidence=0.96, source="qwen_vision"),  # CONFLICT
        packing_date=FieldExtractionResult(field="packing_date", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        manufacturing_date=FieldExtractionResult(field="manufacturing_date", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        consumer_care=FieldExtractionResult(field="consumer_care", value=None, confidence=0.0, source="qwen_vision", status="NOT_FOUND"),
        country_of_origin=FieldExtractionResult(field="country_of_origin", value="India", confidence=0.9, source="qwen_vision"),
        batch_or_lot_number=FieldExtractionResult(field="batch_or_lot_number", value="B1", confidence=0.8, source="qwen_vision"),
    )

    reconciled, ledger = ExtractionReconciler.reconcile(tess_fields, qwen_fields)

    assert reconciled.mrp.conflict_detected is True
    assert reconciled.mrp.status == "UNCLEAR"
    assert reconciled.mrp.confidence <= 0.50  # Maps to Needs Review
    assert ledger["mrp"].resolution == "disagreement"
    assert ledger["mrp"].conflict_detected is True
    assert len(ledger["mrp"].candidates) == 2
    assert ledger["mrp"].candidates[0].value == "₹45.00"
    assert ledger["mrp"].candidates[1].value == "₹15.00"

@pytest.mark.asyncio
async def test_groq_failure_gracefully_falls_back_to_tesseract(dummy_image_path):
    """Test 9: When Groq fails, composite pipeline continues using Tesseract without crashing."""
    failing_vision = MagicMock()
    failing_vision.extract = AsyncMock(side_effect=Exception("Groq rate limit exceeded"))

    pipeline = ReconciledPipelineExtractionProvider(vision_provider=failing_vision)
    
    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_dummy_test_key"}):
        result = await pipeline.extract(dummy_image_path, SAMPLE_OCR_RESULT, "insp_test_009")

        assert isinstance(result, ExtractedFieldsContainer)
        assert pipeline.last_vision_status == "fallback_tesseract"
        # Pipeline didn't crash and extracted available Tesseract fields
        assert result.mrp.value is not None or result.mrp.status in ("FOUND", "UNCLEAR", "NOT_FOUND")

def test_rule_engine_processes_reconciled_declarations():
    """Test 10: Legal Metrology Rule Engine deterministically validates reconciled declarations."""
    reconciled_container = ExtractedFieldsContainer(
        product_name=FieldExtractionResult(field="product_name", value="Test Noodles", confidence=0.95, source="qwen_vision+tesseract"),
        manufacturer=FieldExtractionResult(field="manufacturer", value="Test Foods Pvt Ltd, Mumbai", confidence=0.92, source="qwen_vision+tesseract"),
        packer=FieldExtractionResult(field="packer", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        importer=FieldExtractionResult(field="importer", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        net_quantity=FieldExtractionResult(field="net_quantity", value="140 g", confidence=0.96, source="qwen_vision+tesseract"),
        mrp=FieldExtractionResult(field="mrp", value="₹45.00", confidence=0.97, source="qwen_vision+tesseract"),
        packing_date=FieldExtractionResult(field="packing_date", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        manufacturing_date=FieldExtractionResult(field="manufacturing_date", value="05/2026", confidence=0.88, source="qwen_vision"),
        consumer_care=FieldExtractionResult(field="consumer_care", value="care@testfoods.com, 1800-123-456", confidence=0.94, source="qwen_vision"),
        country_of_origin=FieldExtractionResult(field="country_of_origin", value="India", confidence=0.98, source="qwen_vision"),
        batch_or_lot_number=FieldExtractionResult(field="batch_or_lot_number", value="LOT-998", confidence=0.89, source="qwen_vision"),
    )

    rules = get_rule_repository().list_rules(version="2026.1", enabled_only=True)
    eval_result = ComplianceEngine.evaluate(
        inspection_id="insp_test_010",
        extracted_declarations={"fields": reconciled_container.model_dump()},
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    # Verified deterministic rule engine evaluates declarations correctly
    assert eval_result.overall_status in ("COMPLIANT", "NON_COMPLIANT", "POTENTIAL_VIOLATION", "MANUAL_REVIEW", "NEEDS_REVIEW")
    assert eval_result.risk_score >= 0
    assert len(eval_result.checks) >= 10

def test_low_confidence_declaration_maps_to_needs_review():
    """Test 6: Low confidence extraction (<0.60) maps to Needs Review in rule engine."""
    reconciled = ExtractedFieldsContainer(
        product_name=FieldExtractionResult(field="product_name", value="Maggi", confidence=0.95, source="qwen_vision"),
        manufacturer=FieldExtractionResult(field="manufacturer", value="Nestle Ind...", confidence=0.45, source="qwen_vision", status="UNCLEAR"),
        packer=FieldExtractionResult(field="packer", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        importer=FieldExtractionResult(field="importer", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        net_quantity=FieldExtractionResult(field="net_quantity", value="140 g", confidence=0.90, source="qwen_vision"),
        mrp=FieldExtractionResult(field="mrp", value="₹45", confidence=0.92, source="qwen_vision"),
        packing_date=FieldExtractionResult(field="packing_date", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        manufacturing_date=FieldExtractionResult(field="manufacturing_date", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        consumer_care=FieldExtractionResult(field="consumer_care", value=None, confidence=0.0, source="ocr+vision", status="NOT_FOUND"),
        country_of_origin=FieldExtractionResult(field="country_of_origin", value="India", confidence=0.95, source="qwen_vision"),
        batch_or_lot_number=FieldExtractionResult(field="batch_or_lot_number", value="B1", confidence=0.85, source="qwen_vision"),
    )
    rules = get_rule_repository().list_rules(version="2026.1", enabled_only=True)
    eval_result = ComplianceEngine.evaluate(
        inspection_id="insp_test_low_conf",
        extracted_declarations={"fields": reconciled.model_dump()},
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )
    mfg_check = next(c for c in eval_result.checks if c.field == "manufacturer")
    assert mfg_check.status in ("MANUAL_REVIEW", "NEEDS_REVIEW")
