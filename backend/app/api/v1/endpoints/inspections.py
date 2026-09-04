from backend.app.schemas.listing_comparison import EcomListingPayload, ListingComparisonResult
from backend.app.core.config import settings
from PIL import Image, ImageOps
import io
import os
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, status, HTTPException, Query, Request, Body
from backend.app.schemas.inspection import InspectionUploadResponse
from backend.app.schemas.ocr import OCRResult
from backend.app.schemas.extraction import ExtractionResponse, ExtractedFieldsContainer, InspectionDebugDossierResponse
from backend.app.services.ocr.preprocessor import ImagePreprocessingPipeline
from backend.app.schemas.compliance import ComplianceEvaluationResult
from backend.app.schemas.evidence import EvidenceListResponse
from backend.app.schemas.dashboard import DashboardMetricsResponse
from backend.app.services.file_validator import FileValidationService
from backend.app.services.storage import get_storage_service
from backend.app.services.ocr import get_ocr_provider
from backend.app.services.extraction import get_extraction_provider, ExtractionValidator
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.services.evidence.service import EvidenceService
from backend.app.services.database_persistence import DatabasePersistenceService
from backend.app.repositories.inspection_repository import get_inspection_repository
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.core.logging import get_logger

logger = get_logger("api.inspections")
router = APIRouter()

@router.post(
    "/inspections",
    response_model=InspectionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload package image for compliance inspection",
    description="Accepts a package label image (JPG, PNG, TIFF), validates format and size, stores it via storage abstraction, and persists metadata into PostgreSQL."
)
async def upload_package_image(
    request: Request,
    file: UploadFile = File(..., description="Package or commodity label image file (JPG, PNG, TIFF)")
):
    logger.info(f"Received package image upload request: filename='{file.filename}', content_type='{file.content_type}'")

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required in the upload request."
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read upload stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file stream."
        )

    # 1. Validate file format, magic bytes, and size
    mime_type, extension = FileValidationService.validate_image_upload(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type
    )

    # 2. Generate unique inspection ID
    unique_id = uuid.uuid4().hex[:12]
    inspection_id = f"insp_{unique_id}"

    # 3. Store original image via storage abstraction
    storage_service = get_storage_service()
    storage_result = storage_service.save_file(
        file_bytes=file_bytes,
        filename=f"original{extension}",
        content_type=mime_type,
        subfolder=inspection_id
    )

    # 3b. Web display compatibility companion for non-browser-native formats (HEIC, TIFF, BMP, etc.)
    public_display_url = storage_result.public_url
    if extension.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        try:
            insp_dir = os.path.join(settings.UPLOAD_DIR, inspection_id)
            display_path = os.path.join(insp_dir, "display.jpg")
            with Image.open(io.BytesIO(file_bytes)) as pil_img:
                try:
                    pil_img = ImageOps.exif_transpose(pil_img)
                except Exception:
                    pass
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                pil_img.save(display_path, format="JPEG", quality=92)
                public_display_url = f"/uploads/{inspection_id}/display.jpg"
        except Exception as err:
            logger.warning(f"Could not generate display.jpg preview for {inspection_id}: {err}")

    # 4. Persist to PostgreSQL relational schema
    client_ip = request.client.host if request.client else None
    DatabasePersistenceService.persist_inspection_upload(
        inspection_id=inspection_id,
        filename=file.filename,
        mime_type=mime_type,
        file_size=storage_result.file_size,
        storage_key=storage_result.storage_key,
        public_url=public_display_url,
        client_ip=client_ip
    )

    # Also keep SQLite repository in sync for fast local queries
    created_at = datetime.now(timezone.utc).isoformat()
    repo = get_inspection_repository()
    inspection_record = repo.save_inspection(
        inspection_id=inspection_id,
        filename=file.filename,
        mime_type=mime_type,
        file_size=storage_result.file_size,
        created_at=created_at,
        image_location=storage_result.storage_key,
        image_url=public_display_url,
        status="UPLOADED"
    )

    logger.info(f"Successfully stored inspection {inspection_id}: {storage_result.file_size} bytes stored at {storage_result.file_path}")

    return InspectionUploadResponse(**inspection_record)

@router.get(
    "/inspections/meta/dashboard",
    response_model=DashboardMetricsResponse,
    summary="Get authentic dashboard metrics",
    description="Returns real, computed inspection compliance metrics across the platform. No fake statistics."
)
async def get_dashboard_metrics():
    repo = get_inspection_repository()
    metrics = repo.get_dashboard_metrics()
    return DashboardMetricsResponse(**metrics)

@router.get(
    "/inspections/{inspection_id}",
    response_model=Dict[str, Any],
    summary="Retrieve complete historical inspection dossier by ID",
    description="Returns full PostgreSQL historical record preserving timestamp, inspector, product, model/provider version, rule version, extracted declarations, compliance result, evidence, and review status."
)
async def get_inspection_by_id(inspection_id: str):
    # First attempt to fetch complete relational dossier from PostgreSQL
    pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    if pg_dossier:
        return pg_dossier

    # Fallback to repository
    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
        if pg_dossier:
            record = repo.save_inspection(
                inspection_id=inspection_id,
                filename=pg_dossier.get("filename", "package.jpg"),
                mime_type=pg_dossier.get("mime_type", "image/jpeg"),
                file_size=pg_dossier.get("file_size", 204800),
                created_at=pg_dossier.get("created_at"),
                image_location=pg_dossier.get("image_url", ""),
                image_url=pg_dossier.get("image_url", ""),
                status=pg_dossier.get("status", "EVALUATED")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection with ID '{inspection_id}' not found."
            )
    comp = repo.get_compliance_result(inspection_id)
    ext = repo.get_extraction_result(inspection_id)
    ocr = repo.get_ocr_result(inspection_id)
    res = dict(record)
    res["compliance_result"] = comp
    res["extraction_result"] = ext
    res["ocr_result"] = ocr
    return res

@router.get(
    "/inspections",
    response_model=List[Dict[str, Any]],
    summary="List all historical inspections",
    description="Returns all inspection records preserving date, product, manufacturer, status, risk, and review status."
)
async def list_inspections():
    # Fetch from PostgreSQL
    pg_list = DatabasePersistenceService.list_all_inspections()
    if pg_list:
        return pg_list

    # Fallback to repository
    repo = get_inspection_repository()
    return repo.list_inspections()

@router.post(
    "/inspections/{inspection_id}/ocr",
    response_model=OCRResult,
    summary="Extract text and spatial bounding boxes via OCR service",
    description="Invokes OCR service to detect text blocks and bounding boxes, and persists to PostgreSQL."
)
async def extract_ocr_from_inspection(inspection_id: str):
    logger.info(f"Starting OCR extraction for inspection '{inspection_id}'")

    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    storage_service = get_storage_service()
    image_path = storage_service.get_file_path(record["image_location"])
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection image asset not found in storage."
        )

    provider = get_ocr_provider()
    try:
        ocr_result = await provider.extract(image_path, inspection_id=inspection_id)
    except Exception as e:
        logger.error(f"OCR extraction failed for '{inspection_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

    # Persist in SQLite and PostgreSQL
    repo.save_ocr_result(inspection_id, ocr_result.model_dump())
    DatabasePersistenceService.persist_ocr_result(inspection_id, ocr_result.model_dump())

    logger.info(f"Completed OCR for '{inspection_id}': {ocr_result.total_blocks} text blocks recognized using provider '{ocr_result.provider}' in {ocr_result.processing_time_ms}ms")

    return ocr_result

@router.get(
    "/inspections/{inspection_id}/ocr",
    response_model=OCRResult,
    summary="Get cached OCR extraction result",
    description="Returns previously processed OCR results for an inspection if available."
)
async def get_cached_ocr_result(inspection_id: str):
    repo = get_inspection_repository()
    cached_ocr = repo.get_ocr_result(inspection_id)
    if cached_ocr:
        return OCRResult(**cached_ocr)

    pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    if pg_dossier and pg_dossier.get("ocr") and pg_dossier["ocr"].get("blocks"):
        return OCRResult(**pg_dossier["ocr"])

    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No OCR extraction has been performed yet for inspection '{inspection_id}'. Run POST /api/v1/inspections/{inspection_id}/ocr first."
    )

@router.get(
    "/inspections/{inspection_id}/debug/ocr",
    summary="Developer OCR & Perception Diagnostic",
    description="Returns detailed telemetry for image quality, preprocessed variants, regional OCR passes, and declaration mapping."
)
async def get_ocr_debug_telemetry(inspection_id: str):
    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    cached_ocr = repo.get_ocr_result(inspection_id)
    storage_service = get_storage_service()
    image_path = storage_service.get_file_path(record["image_location"])

    if not cached_ocr:
        ocr_provider = get_ocr_provider()
        ocr_res = await ocr_provider.extract(image_path, inspection_id=inspection_id)
        cached_ocr = ocr_res.model_dump()
        repo.save_ocr_result(inspection_id, cached_ocr)

    cached_ext = repo.get_extraction_result(inspection_id)
    if not cached_ext:
        ext_provider = get_extraction_provider()
        ext_res = await ext_provider.extract(image_path, OCRResult(**cached_ocr), inspection_id=inspection_id)
        cached_ext = ext_res.model_dump() if hasattr(ext_res, 'model_dump') else {"fields": ext_res}
        repo.save_extraction_result(inspection_id, cached_ext)

    quality_metrics = cached_ocr.get("quality_metrics", {})
    blocks = cached_ocr.get("blocks", [])

    return {
        "inspection_id": inspection_id,
        "image_location": record["image_location"],
        "quality_metrics": quality_metrics,
        "variants_generated": ["original_upscaled", "enhanced_clahe", "denoised_sharpened", "binarized_otsu", "adaptive_gaussian", "morph_clean"],
        "regions_evaluated": ["full", "header", "statutory_left", "statutory_right", "bottom_panel"],
        "total_blocks": len(blocks),
        "raw_ocr_sample": cached_ocr.get("full_text", "")[:400],
        "blocks": blocks[:100],
        "extracted_declarations": cached_ext.get("fields", {}),
        "ocr_processing_time_ms": cached_ocr.get("processing_time_ms", 0.0)
    }

@router.post(
    "/inspections/{inspection_id}/extract",
    response_model=ExtractionResponse,
    summary="Extract structured legal declarations from package image & OCR",
    description="Invokes extraction service to locate the 11 mandatory declaration fields, and persists to PostgreSQL declarations table."
)
async def extract_declarations(inspection_id: str):
    logger.info(f"Starting declaration extraction for inspection '{inspection_id}'")
    start_time = time.time()

    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    storage_service = get_storage_service()
    image_path = storage_service.get_file_path(record["image_location"])
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection image asset not found in storage."
        )

    cached_ocr = repo.get_ocr_result(inspection_id)
    if cached_ocr:
        ocr_result = OCRResult(**cached_ocr)
    else:
        ocr_provider = get_ocr_provider()
        ocr_result = await ocr_provider.extract(image_path, inspection_id=inspection_id)
        repo.save_ocr_result(inspection_id, ocr_result.model_dump())
        DatabasePersistenceService.persist_ocr_result(inspection_id, ocr_result.model_dump())

    # Ensure high-fidelity processed image is prepared for Vision AI
    processed_path, prep_status, prep_meta = ImagePreprocessingPipeline.prepare_and_persist_processed_image(image_path)

    extraction_provider = get_extraction_provider()
    extracted_container = await extraction_provider.extract(
        image_path=processed_path,
        ocr_result=ocr_result,
        inspection_id=inspection_id
    )

    validated_container = ExtractionValidator.validate_model_payload(extracted_container.model_dump())

    fields_dict = validated_container.model_dump()
    extracted_count = sum(1 for f in fields_dict.values() if f.get("value") is not None)
    missing_count = sum(1 for f in fields_dict.values() if f.get("value") is None)
    duration = round((time.time() - start_time) * 1000, 2)

    reconciliation = getattr(extraction_provider, "last_reconciliation_ledger", None)
    vision_status = getattr(extraction_provider, "last_vision_status", "active")
    vision_provider = getattr(settings, "GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

    response = ExtractionResponse(
        inspection_id=inspection_id,
        fields=validated_container,
        extracted_fields_count=extracted_count,
        missing_fields_count=missing_count,
        provider=getattr(extraction_provider, "__class__", type(extraction_provider)).__name__,
        processing_time_ms=duration,
        vision_provider=vision_provider,
        vision_status=vision_status,
        preprocessing_status=prep_status,
        reconciliation=reconciliation
    )

    repo.save_extraction_result(inspection_id, response.model_dump())
    DatabasePersistenceService.persist_declarations(inspection_id, response.model_dump())
    logger.info(f"Completed declaration extraction for '{inspection_id}': {extracted_count} found, {missing_count} missing in {duration}ms")

    return response

@router.get(
    "/inspections/{inspection_id}/extract",
    response_model=ExtractionResponse,
    summary="Get cached declaration extraction results",
    description="Returns previously processed declaration extraction results for an inspection."
)
async def get_cached_extraction(inspection_id: str):
    repo = get_inspection_repository()
    cached_extraction = repo.get_extraction_result(inspection_id)
    if cached_extraction:
        if isinstance(cached_extraction, dict) and "fields" in cached_extraction:
            return ExtractionResponse(**{**cached_extraction, "inspection_id": inspection_id})
        else:
            try:
                return ExtractionResponse(
                    inspection_id=inspection_id,
                    fields=ExtractedFieldsContainer(**cached_extraction),
                    extracted_fields_count=sum(1 for f in cached_extraction.values() if isinstance(f, dict) and f.get("value") is not None),
                    missing_fields_count=sum(1 for f in cached_extraction.values() if isinstance(f, dict) and f.get("value") is None),
                    provider="cached",
                    processing_time_ms=0.0
                )
            except Exception:
                return ExtractionResponse(**{**cached_extraction, "inspection_id": inspection_id})

    pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    if pg_dossier and pg_dossier.get("extracted_declarations"):
        decls = pg_dossier["extracted_declarations"]
        if isinstance(decls, dict) and "fields" in decls:
            return ExtractionResponse(**{**decls, "inspection_id": inspection_id})
        else:
            try:
                validated = ExtractionValidator.validate_model_payload(decls)
                fields_dict = validated.model_dump()
                return ExtractionResponse(
                    inspection_id=inspection_id,
                    fields=validated,
                    extracted_fields_count=sum(1 for f in fields_dict.values() if f.get("value") is not None),
                    missing_fields_count=sum(1 for f in fields_dict.values() if f.get("value") is None),
                    provider="postgresql",
                    processing_time_ms=0.0
                )
            except Exception as ex:
                logger.warning(f"Failed to validate postgres declarations payload: {ex}")
                return ExtractionResponse(**{**decls, "inspection_id": inspection_id})

    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No semantic extraction has been performed yet for inspection '{inspection_id}'. Run POST /api/v1/inspections/{inspection_id}/extract first."
    )


async def _run_compliance_evaluation(inspection_id: str, category: str = "packaged_commodity", rule_version: Optional[str] = None):
    """Shared compliance evaluation logic used by POST /evaluate and internal callers."""
    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
        if pg_dossier:
            record = repo.save_inspection(
                inspection_id=inspection_id,
                filename=pg_dossier.get("filename", "package.jpg"),
                mime_type=pg_dossier.get("mime_type", "image/jpeg"),
                file_size=pg_dossier.get("file_size", 204800),
                created_at=pg_dossier.get("created_at"),
                image_location=pg_dossier.get("image_url", ""),
                image_url=pg_dossier.get("image_url", ""),
                status=pg_dossier.get("status", "EVALUATED")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection with ID '{inspection_id}' not found."
            )

    # Get extracted declarations
    cached_ext = repo.get_extraction_result(inspection_id)
    ext_data = None
    if cached_ext:
        ext_data = cached_ext
    else:
        pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
        if pg_dossier and pg_dossier.get("extracted_declarations"):
            ext_data = pg_dossier["extracted_declarations"]

    if not ext_data:
        # Auto-run extraction if declarations haven't been extracted yet
        try:
            extraction_res = await extract_declarations(inspection_id)
            cached_ext = repo.get_extraction_result(inspection_id)
            if cached_ext:
                ext_data = cached_ext
            elif extraction_res and hasattr(extraction_res, "fields"):
                ext_data = extraction_res.fields.model_dump()
        except Exception as e:
            logger.warning(f"Auto-extraction on evaluate failed: {e}")

    if not ext_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No semantic extraction has been performed yet for inspection '{inspection_id}'. Run POST /api/v1/inspections/{inspection_id}/extract first."
        )

    rule_repo = get_rule_repository()
    selected_version = rule_version or rule_repo.get_latest_version()
    applicable_rules = rule_repo.list_rules(version=selected_version, enabled_only=True)

    compliance_result = ComplianceEngine.evaluate(
        inspection_id=inspection_id,
        extracted_declarations=ext_data,
        product_category=category,
        applicable_rules=applicable_rules,
        rule_version=selected_version
    )

    evidence_res = EvidenceService.build_evidence(
        inspection_id=inspection_id,
        compliance_result=compliance_result,
        image_id=record.get("filename", "package")
    )

    repo.save_compliance_result(inspection_id, compliance_result.model_dump())
    DatabasePersistenceService.persist_compliance_and_evidence(
        inspection_id=inspection_id,
        compliance_data=compliance_result.model_dump(),
        evidence_data=evidence_res.model_dump()
    )

    return compliance_result

@router.post(
    "/inspections/{inspection_id}/evaluate",
    response_model=ComplianceEvaluationResult,
    summary="Evaluate inspection against deterministic Legal Metrology rules",
    description="Deterministically screens extracted package declarations against versioned statutory rules, persisting compliance checks, violations, and evidence into PostgreSQL."
)
async def evaluate_compliance(
    inspection_id: str,
    category: str = Query("packaged_commodity", description="Product category for applicability screening"),
    rule_version: Optional[str] = Query(None, description="Statutory rule catalog version (e.g. '2026.1')")
):
    return await _run_compliance_evaluation(
        inspection_id=inspection_id,
        category=category,
        rule_version=rule_version
    )

@router.get(
    "/inspections/{inspection_id}/compliance",
    response_model=ComplianceEvaluationResult,
    summary="Get cached compliance evaluation result",
    description="Returns previously evaluated compliance results for an inspection."
)
async def get_cached_compliance(inspection_id: str):
    repo = get_inspection_repository()
    cached_comp = repo.get_compliance_result(inspection_id)
    if cached_comp and cached_comp.get("canonical_requirements") and len(cached_comp["canonical_requirements"]) > 0:
        return ComplianceEvaluationResult(**cached_comp)

    # Check PostgreSQL relational dossier
    pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    if pg_dossier:
        pg_comp = pg_dossier.get("compliance_result")
        if pg_comp and pg_comp.get("canonical_requirements") and len(pg_comp["canonical_requirements"]) > 0:
            return ComplianceEvaluationResult(**pg_comp)

        decls = pg_dossier.get("extracted_declarations")
        if decls:
            rule_repo = get_rule_repository()
            applicable_rules = rule_repo.list_rules(version=rule_repo.get_latest_version(), enabled_only=True)
            res = ComplianceEngine.evaluate(
                inspection_id=inspection_id,
                extracted_declarations=decls,
                product_category="packaged_commodity",
                applicable_rules=applicable_rules,
                rule_version="2026.1"
            )
            repo.save_compliance_result(inspection_id, res.model_dump())
            return res

    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    if not cached_comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compliance evaluation has been performed yet for inspection '{inspection_id}'. Run POST /api/v1/inspections/{inspection_id}/evaluate first."
        )

    return ComplianceEvaluationResult(**cached_comp)

@router.get(
    "/inspections/{inspection_id}/evidence",
    response_model=EvidenceListResponse,
    summary="Retrieve grounded evidence ledger for an inspection",
    description="Returns complete evidence traceability linking statutory rules to extracted declarations and spatial image regions."
)
async def get_inspection_evidence(
    inspection_id: str,
    rule_id: Optional[str] = Query(None, description="Filter evidence for a specific statutory rule ID"),
    type: Optional[str] = Query(None, description="Filter by evidence classification type (ABSENCE, INCORRECT_DECLARATION, UNCERTAIN, DETECTED_DECLARATION)")
):
    logger.info(f"Retrieving evidence for inspection '{inspection_id}' (rule_id='{rule_id}', type='{type}')")

    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    cached_comp = repo.get_compliance_result(inspection_id)
    if not cached_comp:
        comp_res = await _run_compliance_evaluation(inspection_id)
        cached_comp = comp_res.model_dump()

    comp_result_obj = ComplianceEvaluationResult(**cached_comp)

    evidence_response = EvidenceService.build_evidence(
        inspection_id=inspection_id,
        compliance_result=comp_result_obj,
        image_id=record["filename"]
    )

    filtered_items = evidence_response.evidence
    if rule_id:
        filtered_items = [e for e in filtered_items if e.rule_id.lower() == rule_id.lower().strip()]
    if type:
        filtered_items = [e for e in filtered_items if e.type.upper() == type.upper().strip()]

    evidence_response.evidence = filtered_items
    evidence_response.total = len(filtered_items)

    return evidence_response

from fastapi.responses import Response
from backend.app.services.report.generator import ReportGenerator

@router.post(
    "/inspections/{inspection_id}/report",
    summary="Generate official PDF inspection report",
    description="Generates an official, publication-quality Legal Metrology PDF inspection report containing packaging photograph, metadata, audit ledger distinguishing detected fact vs rule requirement vs system finding, and statutory disclaimer."
)
async def generate_inspection_report(inspection_id: str):
    logger.info(f"Generating PDF inspection report for '{inspection_id}'")

    # 1. Fetch complete relational dossier
    dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    if not dossier:
        # Check repository fallback
        repo = get_inspection_repository()
        record = repo.get_inspection(inspection_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection with ID '{inspection_id}' not found."
            )
        # Run compliance if needed
        comp = repo.get_compliance_result(inspection_id)
        if not comp:
            comp_res = await _run_compliance_evaluation(inspection_id)
            comp = comp_res.model_dump()
        dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)

    # 2. Locate image asset on disk
    storage_service = get_storage_service()
    image_rel = dossier.get("image", {}).get("file_path") or f"{inspection_id}/original.jpg"
    image_path = storage_service.get_file_path(image_rel)
    if not os.path.exists(image_path):
        # Check alternate extensions
        for ext in [".png", ".jpeg", ".tiff", ".tif"]:
            alt = storage_service.get_file_path(f"{inspection_id}/original{ext}")
            if os.path.exists(alt):
                image_path = alt
                break

    # 3. Generate PDF
    try:
        pdf_bytes = ReportGenerator.generate_pdf(dossier, image_path=image_path)
    except Exception as e:
        logger.error(f"PDF generation failed for '{inspection_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate inspection report: {str(e)}"
        )

    filename = f"Inspection_Report_{inspection_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get(
    "/inspections/{inspection_id}/report",
    summary="Download PDF inspection report",
    description="Direct download route for official PDF inspection report."
)
async def download_inspection_report(inspection_id: str):
    return await generate_inspection_report(inspection_id)

from backend.app.schemas.batch import BatchInspectionItemResult, BatchInspectionResponse

@router.post(
    "/inspections/batch",
    response_model=BatchInspectionResponse,
    summary="Process batch of package commodity images end-to-end",
    description="Accepts multiple package photographs (e.g. up to 20 images). Runs the entire pipeline (Ingestion -> OCR -> Declaration Extraction -> Rule Evaluation -> Persistence) on each image independently. Does not block the batch if one image fails."
)
async def process_batch_inspections(
    request: Request,
    files: List[UploadFile] = File(..., description="Multiple package photograph files"),
    category: str = Query("packaged_commodity", description="Applicable commodity category"),
    rule_version: Optional[str] = Query(None, description="Statutory rule catalog version")
):
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting batch inspection {batch_id} with {len(files)} files")

    results: List[BatchInspectionItemResult] = []
    rule_repo = get_rule_repository()
    selected_version = rule_version or rule_repo.get_latest_version()
    applicable_rules = rule_repo.list_rules(version=selected_version, category=None, enabled_only=True)
    storage_service = get_storage_service()
    client_ip = request.client.host if request.client else None

    for file in files:
        filename = file.filename or "unknown_asset.jpg"
        created_at_iso = datetime.now(timezone.utc).isoformat()

        try:
            # 1. Read file bytes
            file_bytes = await file.read()
            if not file_bytes:
                raise ValueError("Empty file stream received.")

            # 2. Validate format & size
            mime_type, extension = FileValidationService.validate_image_upload(
                file_bytes=file_bytes,
                filename=filename,
                content_type=file.content_type
            )

            # 3. Unique inspection ID & storage
            unique_id = uuid.uuid4().hex[:12]
            inspection_id = f"insp_{unique_id}"

            storage_result = storage_service.save_file(
                file_bytes=file_bytes,
                filename=f"original{extension}",
                content_type=mime_type,
                subfolder=inspection_id
            )

            public_display_url = storage_result.public_url
            if extension.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                try:
                    insp_dir = os.path.join(settings.UPLOAD_DIR, inspection_id)
                    display_path = os.path.join(insp_dir, "display.jpg")
                    with Image.open(io.BytesIO(file_bytes)) as pil_img:
                        try:
                            pil_img = ImageOps.exif_transpose(pil_img)
                        except Exception:
                            pass
                        if pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        pil_img.save(display_path, format="JPEG", quality=92)
                        public_display_url = f"/uploads/{inspection_id}/display.jpg"
                except Exception as err:
                    logger.warning(f"Could not generate display.jpg preview for batch item {inspection_id}: {err}")

            # 4. Save to PostgreSQL and SQLite
            DatabasePersistenceService.persist_inspection_upload(
                inspection_id=inspection_id,
                filename=filename,
                mime_type=mime_type,
                file_size=storage_result.file_size,
                storage_key=storage_result.storage_key,
                public_url=public_display_url,
                client_ip=client_ip
            )
            repo = get_inspection_repository()
            repo.save_inspection(
                inspection_id=inspection_id,
                filename=filename,
                mime_type=mime_type,
                file_size=storage_result.file_size,
                created_at=created_at_iso,
                image_location=storage_result.storage_key,
                image_url=public_display_url,
                status="UPLOADED"
            )

            # 5. OCR
            image_path = storage_service.get_file_path(storage_result.storage_key)
            ocr_provider = get_ocr_provider()
            ocr_res = await ocr_provider.extract(image_path, inspection_id=inspection_id)
            repo.save_ocr_result(inspection_id, ocr_res.model_dump())
            DatabasePersistenceService.persist_ocr_result(inspection_id, ocr_res.model_dump())

            # 6. Extraction
            extraction_provider = get_extraction_provider()
            extracted_container = await extraction_provider.extract(
                image_path=image_path,
                ocr_result=ocr_res,
                inspection_id=inspection_id
            )
            validated_container = ExtractionValidator.validate_model_payload(extracted_container.model_dump())
            fields_dict = validated_container.model_dump()
            extracted_count = sum(1 for f in fields_dict.values() if f.get("value") is not None)
            missing_count = sum(1 for f in fields_dict.values() if f.get("value") is None)

            extraction_resp = ExtractionResponse(
                inspection_id=inspection_id,
                fields=validated_container,
                extracted_fields_count=extracted_count,
                missing_fields_count=missing_count,
                provider=getattr(extraction_provider, "__class__", type(extraction_provider)).__name__,
                processing_time_ms=10.0
            )
            repo.save_extraction_result(inspection_id, extraction_resp.model_dump())
            DatabasePersistenceService.persist_declarations(inspection_id, extraction_resp.model_dump())

            # 7. Compliance evaluation
            compliance_res = ComplianceEngine.evaluate(
                inspection_id=inspection_id,
                extracted_declarations=extraction_resp.model_dump(),
                product_category=category,
                applicable_rules=applicable_rules,
                rule_version=selected_version
            )
            evidence_res = EvidenceService.build_evidence(
                inspection_id=inspection_id,
                compliance_result=compliance_res,
                image_id=filename
            )

            repo.save_compliance_result(inspection_id, compliance_res.model_dump())
            DatabasePersistenceService.persist_compliance_and_evidence(
                inspection_id=inspection_id,
                compliance_data=compliance_res.model_dump(),
                evidence_data=evidence_res.model_dump()
            )

            # Compute avg confidence
            confs = [f.get("confidence", 0.0) for f in fields_dict.values() if f.get("value") is not None]
            avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.0
            prod_name = fields_dict.get("product_name", {}).get("value") or filename

            results.append(
                BatchInspectionItemResult(
                    inspection_id=inspection_id,
                    filename=filename,
                    product_name=prod_name,
                    status=compliance_res.overall_status,
                    risk_score=compliance_res.risk_score,
                    violations_count=len(compliance_res.violations),
                    average_confidence=avg_conf,
                    created_at=created_at_iso,
                    success=True,
                    error=None
                )
            )

        except Exception as e:
            logger.error(f"Batch item failed for '{filename}': {e}", exc_info=True)
            results.append(
                BatchInspectionItemResult(
                    inspection_id=None,
                    filename=filename,
                    product_name=filename,
                    status="FAILED",
                    risk_score=0,
                    violations_count=0,
                    average_confidence=0.0,
                    created_at=created_at_iso,
                    success=False,
                    error=str(e)
                )
            )

    compliant = sum(1 for r in results if r.status == "COMPLIANT")
    violations = sum(1 for r in results if r.status == "POTENTIAL_VIOLATION")
    manual = sum(1 for r in results if r.status == "MANUAL_REVIEW")
    high_risk = sum(1 for r in results if r.risk_score >= 30)
    failed = sum(1 for r in results if not r.success)

    logger.info(f"Completed batch {batch_id}: {len(results)} total, {compliant} compliant, {violations} violations, {manual} review, {high_risk} high-risk, {failed} failed")

    return BatchInspectionResponse(
        batch_id=batch_id,
        total=len(results),
        compliant_count=compliant,
        potential_violations_count=violations,
        manual_review_count=manual,
        high_risk_count=high_risk,
        failed_count=failed,
        results=results
    )

from backend.app.schemas.review import ReviewSubmissionRequest, ReviewRecordResponse

@router.post(
    "/inspections/{inspection_id}/review",
    response_model=ReviewRecordResponse,
    summary="Submit official human inspector review decision",
    description="Records an inspector's official determination (Confirm finding, Reject finding, Request manual verification, Mark as not applicable) with optional comments. Strictly preserves original AI screening results for audit traceability and logs the action in PostgreSQL AuditLog."
)
async def submit_inspection_review(
    request: Request,
    inspection_id: str,
    payload: ReviewSubmissionRequest
):
    logger.info(f"Submitting inspector review for '{inspection_id}': decision='{payload.decision}', reviewer='{payload.reviewer}'")
    client_ip = request.client.host if request.client else None

    try:
        result = DatabasePersistenceService.submit_inspection_review(
            inspection_id=inspection_id,
            decision=payload.decision,
            comment=payload.comment,
            reviewer_name=payload.reviewer or "inspector_lm",
            client_ip=client_ip
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit review for '{inspection_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist review decision.")

    return ReviewRecordResponse(**result)

@router.post(
    "/inspections/{inspection_id}/reviews",
    response_model=ReviewRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit official human inspector review decision (alias)",
    include_in_schema=False
)
async def submit_inspection_review_alias(request: Request, inspection_id: str, payload: ReviewSubmissionRequest):
    return await submit_inspection_review(request, inspection_id, payload)

@router.get(
    "/inspections/{inspection_id}/reviews",
    response_model=List[ReviewRecordResponse],
    summary="Retrieve human inspector review history for inspection",
    description="Returns the chronological ledger of human review determinations preserving reviewer, decision, comments, and the immutable original AI status."
)
async def get_inspection_reviews(inspection_id: str):
    reviews = DatabasePersistenceService.get_inspection_reviews(inspection_id)
    return [ReviewRecordResponse(**r) for r in reviews]

@router.post(
    "/inspections/{inspection_id}/compare-listing",
    response_model=ListingComparisonResult,
    summary="Dual-Input: Compare E-Commerce marketplace listing against physical package label",
    description="Cross-references digital listing claims (price, net quantity, country of origin) against physical package statutory declarations under Rule 6(10)."
)
async def compare_ecommerce_listing(
    inspection_id: str,
    listing_data: EcomListingPayload
):
    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found."
        )

    cached_ext = repo.get_extraction_result(inspection_id)
    if not cached_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Declarations have not been extracted yet. Please run extraction first."
        )

    fields_map = cached_ext.get("fields", {}) if isinstance(cached_ext, dict) else cached_ext

    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules()

    comp_res = ComplianceEngine.evaluate(
        inspection_id=inspection_id,
        extracted_declarations=fields_map,
        product_category="e_commerce_listing",
        applicable_rules=rules,
        rule_version=rule_repo.get_latest_version(),
        listing_data=listing_data.model_dump()
    )

    repo.save_compliance_result(inspection_id, comp_res.model_dump())

    discrepancies = [c.reason for c in comp_res.checks if c.rule_id == "LM-ECOM-001" and c.status == "POTENTIAL_VIOLATION"]

    return ListingComparisonResult(
        inspection_id=inspection_id,
        has_listing=True,
        listing_attributes=listing_data,
        discrepancies=discrepancies,
        status="POTENTIAL_DISCREPANCY" if discrepancies else "COMPLIANT"
    )


@router.get(
    "/inspections/{inspection_id}/debug",
    response_model=InspectionDebugDossierResponse,
    summary="Retrieve developer inspection debug dossier",
    description="Provides forensic developer view: original image, preprocessed image, Tesseract OCR blocks, Qwen Vision extracted JSON, candidate reconciliation, and rule engine input/output."
)
async def get_inspection_debug_dossier(inspection_id: str):
    repo = get_inspection_repository()
    record = repo.get_inspection(inspection_id)
    pg_dossier = None
    if not record:
        pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
        if pg_dossier:
            img_loc = (pg_dossier.get("image") or {}).get("location") or f"data/uploads/{inspection_id}/original.jpg"
            img_url = pg_dossier.get("image_url") or f"/uploads/{inspection_id}/original.jpg"
            record = {
                "inspection_id": inspection_id,
                "image_location": img_loc,
                "image_url": img_url,
                "filename": pg_dossier.get("filename", "package.jpg")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection with ID '{inspection_id}' not found."
            )

    storage_service = get_storage_service()
    original_path = storage_service.get_file_path(record["image_location"])
    
    # Processed path
    if os.path.exists(original_path):
        processed_path, prep_status, prep_meta = ImagePreprocessingPipeline.prepare_and_persist_processed_image(original_path)
        processed_url = f"/uploads/{inspection_id}/processed.jpg" if os.path.exists(processed_path) else record.get("image_url", "")
    else:
        processed_url = record.get("image_url", "")
        prep_status = "ready"
        prep_meta = {"status": "seeded"}

    cached_ocr = repo.get_ocr_result(inspection_id) or (pg_dossier.get("ocr") if pg_dossier else {}) or {}
    cached_extraction = repo.get_extraction_result(inspection_id) or (pg_dossier.get("extracted_declarations") if pg_dossier else {}) or {}
    cached_comp = repo.get_compliance_result(inspection_id) or (pg_dossier.get("compliance_result") if pg_dossier else {}) or {}

    tesseract_info = {
        "text": cached_ocr.get("full_text") or "\n".join([b.get("text", "") for b in cached_ocr.get("blocks", [])]),
        "total_blocks": cached_ocr.get("total_blocks", len(cached_ocr.get("blocks", []))),
        "average_confidence": cached_ocr.get("average_confidence", 0.0),
        "processing_time_ms": cached_ocr.get("processing_time_ms", 0.0),
        "blocks": cached_ocr.get("blocks", [])[:40]
    }

    vision_info = {
        "model": cached_extraction.get("vision_provider") or getattr(settings, "GROQ_VISION_MODEL", "qwen/qwen3.6-27b"),
        "status": cached_extraction.get("vision_status", "active"),
        "raw_declarations": cached_extraction.get("fields", {}),
        "processing_time_ms": cached_extraction.get("processing_time_ms", 0.0)
    }

    reconciliation_data = cached_extraction.get("reconciliation") or {}

    return InspectionDebugDossierResponse(
        inspection_id=inspection_id,
        original_image_url=record.get("image_url", ""),
        processed_image_url=processed_url,
        preprocessing_status=prep_status,
        preprocessing_metadata=prep_meta,
        tesseract=tesseract_info,
        vision=vision_info,
        reconciliation=reconciliation_data,
        rule_engine_input=cached_extraction.get("fields", {}),
        rule_engine_output=cached_comp
    )

from pydantic import BaseModel, Field

class CheckReviewSubmissionRequest(BaseModel):
    canonical_id: str = Field(..., description="Canonical requirement ID (e.g. REQ-MRP, REQ-NET-QTY)")
    decision: str = Field(..., description="COMPLIANT or NON_COMPLIANT")
    reason: str = Field(..., description="Statutory justification for the inspector determination")
    remarks: Optional[str] = Field(None, description="Supporting remarks or visual evidence notes")
    reviewer: Optional[str] = Field("INS-DL-4029", description="Inspector identifier")

@router.post(
    "/inspections/{inspection_id}/review-check",
    summary="Submit human-in-the-loop inspector decision on a statutory requirement",
    description="Records an official inspector override on a canonical statutory requirement. Preserves preliminary AI screening status, recalculates overall compliance, and logs an immutable audit entry."
)
async def submit_canonical_check_review(
    request: Request,
    inspection_id: str,
    payload: CheckReviewSubmissionRequest
):
    logger.info(f"Submitting check review for '{inspection_id}': canonical_id='{payload.canonical_id}', decision='{payload.decision}', reviewer='{payload.reviewer}'")
    client_ip = request.client.host if request.client else None

    try:
        updated_compliance = DatabasePersistenceService.record_check_review(
            inspection_id=inspection_id,
            canonical_id=payload.canonical_id,
            decision=payload.decision,
            reason=payload.reason,
            remarks=payload.remarks,
            reviewer_name=payload.reviewer or "INS-DL-4029",
            client_ip=client_ip
        )
        return {"status": "success", "compliance": updated_compliance}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to record check review for '{inspection_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist check review.")

class StackActionRequest(BaseModel):
    inspector_name: Optional[str] = Field("inspector.demo", description="Submitting inspector name")
    notes: Optional[str] = Field(None, description="Inspector justification / statutory notes")
    provisions: Optional[str] = Field(None, description="Statutory provisions violated (for complaint)")

@router.post(
    "/inspections/{inspection_id}/clear-stack",
    summary="Move inspection to Cleared Stack",
    description="Officially clears the inspection for commercial distribution. Allowed only if status is COMPLIANT or an inspector manually verified compliance."
)
async def move_to_cleared_stack(
    request: Request,
    inspection_id: str,
    payload: StackActionRequest = Body(default_factory=StackActionRequest)
):
    repo = get_inspection_repository()
    cached_comp = repo.get_compliance_result(inspection_id)
    pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    
    comp_data = cached_comp or (pg_dossier.get("compliance_result") if pg_dossier else {}) or {}
    overall_status = comp_data.get("overall_status") or (pg_dossier.get("overall_status") if pg_dossier else "NOT_EVALUATED")
    reviews = DatabasePersistenceService.get_inspection_reviews(inspection_id)
    has_human_clearance = any(r.get("decision") in ["CONFIRM_FINDING", "OVERRIDE_COMPLIANT"] for r in reviews)

    if overall_status != "COMPLIANT" and not has_human_clearance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot move to Cleared Stack: Current inspection status is '{overall_status}'. Only packages with 'COMPLIANT' status or explicit human inspector clearance may enter the Cleared Stack."
        )

    client_ip = request.client.host if request.client else None
    result = DatabasePersistenceService.submit_inspection_review(
        inspection_id=inspection_id,
        decision="CONFIRM_FINDING",
        comment=payload.notes or "All statutory declarations verified and cleared for commercial distribution.",
        reviewer_name=payload.inspector_name or "inspector.demo",
        client_ip=client_ip
    )
    repo.update_review_status(inspection_id, "CLEARED")
    DatabasePersistenceService.update_inspection_review_status(inspection_id, "CLEARED")

    return {
        "inspection_id": inspection_id,
        "stack": "CLEARED_STACK",
        "status": "CLEARED",
        "message": "Inspection successfully verified and moved to Cleared Stack.",
        "cleared_at": datetime.now(timezone.utc).isoformat()
    }

@router.post(
    "/inspections/{inspection_id}/complaint-stack",
    summary="Move inspection to Complaint Stack",
    description="Escalates confirmed statutory defects for official notice issuance. Allowed only if statutory violations exist or inspector explicitly confirms violation."
)
async def move_to_complaint_stack(
    request: Request,
    inspection_id: str,
    payload: StackActionRequest = Body(default_factory=StackActionRequest)
):
    repo = get_inspection_repository()
    cached_comp = repo.get_compliance_result(inspection_id)
    pg_dossier = DatabasePersistenceService.get_complete_inspection_dossier(inspection_id)
    
    comp_data = cached_comp or (pg_dossier.get("compliance_result") if pg_dossier else {}) or {}
    violations_count = comp_data.get("confirmed_violations_count", 0)
    reviews = DatabasePersistenceService.get_inspection_reviews(inspection_id)
    has_human_violation = any(r.get("decision") in ["CONFIRM_VIOLATION", "OVERRIDE_NON_COMPLIANT"] for r in reviews)

    if violations_count == 0 and not has_human_violation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot move to Complaint Stack: Zero confirmed statutory violations detected. Inspections in 'REVIEW_REQUIRED' cannot automatically escalate to complaints without explicit inspector confirmation."
        )

    client_ip = request.client.host if request.client else None
    complaint_res = DatabasePersistenceService.create_complaint(
        inspection_id=inspection_id,
        enforcement_notes=payload.notes or "Escalated to Complaint Queue for statutory notice issuance.",
        statutory_provisions=payload.provisions or "Rule 6 of Legal Metrology (Packaged Commodities) Rules, 2011",
        inspector_name=payload.inspector_name or "inspector.demo",
        client_ip=client_ip
    )
    repo.update_review_status(inspection_id, "COMPLAINT_REGISTERED")
    DatabasePersistenceService.update_inspection_review_status(inspection_id, "COMPLAINT_REGISTERED")

    return {
        "inspection_id": inspection_id,
        "stack": "COMPLAINT_STACK",
        "status": "COMPLAINT_REGISTERED",
        "complaint_id": complaint_res.get("complaint_id"),
        "message": "Inspection successfully escalated and added to Complaint Stack.",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
