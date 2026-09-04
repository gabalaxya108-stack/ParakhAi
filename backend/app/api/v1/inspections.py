import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from backend.app.core.config import settings
from backend.app.db.repository import InspectionRepository
from backend.app.schemas.inspection import (
    InspectionDetailResponse,
    InspectionSummaryDTO,
    InspectionCreateRequest,
    DeclarationUpdateDTO,
    InspectorReviewRequest
)
from backend.app.services.cv_service import ComputerVisionService
from backend.app.services.ai.factory import get_vision_provider
from backend.app.services.rule_engine.engine import LegalMetrologyRuleEngine
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/inspections", tags=["inspections"])

@router.get("", response_model=List[InspectionSummaryDTO])
async def list_inspections(
    status: Optional[str] = Query(None, description="Filter by status"),
    compliance: Optional[str] = Query(None, description="Filter by compliance verdict")
):
    return InspectionRepository.list_inspections(status_filter=status, compliance_filter=compliance)

@router.get("/{inspection_id}", response_model=InspectionDetailResponse)
async def get_inspection(inspection_id: str):
    insp = InspectionRepository.get_inspection_by_id(inspection_id)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return insp

@router.post("", response_model=InspectionDetailResponse)
async def create_inspection(
    file: Optional[UploadFile] = File(None),
    sample_fixture: Optional[str] = Form(None),
    commodity_name: str = Form("Sample Packaged Commodity"),
    commodity_category: str = Form("Food & Beverages"),
    brand_name: Optional[str] = Form(None),
    batch_number: Optional[str] = Form(None),
    package_width_cm: float = Form(14.0),
    package_height_cm: float = Form(22.0),
    package_depth_cm: Optional[float] = Form(None),
    is_cylindrical: bool = Form(False),
    inspector_name: str = Form("Inspector M. Sharma")
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"pkg_{uuid.uuid4().hex[:8]}.jpg"
    dest_path = os.path.join(settings.UPLOAD_DIR, filename)

    if file and file.filename:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    elif sample_fixture:
        src = os.path.join(settings.FIXTURES_DIR, sample_fixture)
        if os.path.exists(src):
            shutil.copyfile(src, dest_path)
        else:
            raise HTTPException(status_code=400, detail=f"Sample fixture '{sample_fixture}' not found")
    else:
        # Default fallback to potato chips sample
        src = os.path.join(settings.FIXTURES_DIR, "potato_chips_sample.jpg")
        shutil.copyfile(src, dest_path)

    # 1. Computer Vision Preprocessing
    prep_filename = f"prep_{filename}"
    prep_dest = os.path.join(settings.UPLOAD_DIR, prep_filename)
    cv_info = ComputerVisionService.preprocess_image(
        input_image_path=dest_path,
        output_image_path=prep_dest,
        package_width_cm=package_width_cm,
        package_height_cm=package_height_cm,
        is_cylindrical=is_cylindrical
    )

    # 2. AI Extraction Layer (Structured perception only, zero legal judgment)
    provider = get_vision_provider()
    extraction = await provider.extract_declarations(
        image_path=dest_path,
        commodity_category=commodity_category,
        pdp_area_sq_cm=cv_info["pdp_area_sq_cm"],
        mm_per_pixel=cv_info["mm_per_pixel"]
    )

    # 3. Deterministic Versioned Rule Engine (Evaluates Legal Metrology Rules)
    scorecard = LegalMetrologyRuleEngine.evaluate(
        declarations=extraction.declarations,
        pdp_area_sq_cm=cv_info["pdp_area_sq_cm"],
        commodity_category=commodity_category
    )

    # 4. Save to Repository
    req = InspectionCreateRequest(
        commodity_name=extraction.product_name or commodity_name,
        commodity_category=commodity_category,
        brand_name=extraction.brand_name or brand_name,
        batch_number=extraction.batch_lot_number or batch_number,
        package_width_cm=package_width_cm,
        package_height_cm=package_height_cm,
        is_cylindrical=is_cylindrical,
        inspector_name=inspector_name
    )

    resp = InspectionRepository.create_inspection(
        req=req,
        image_url=f"/uploads/{filename}",
        preprocessed_image_url=f"/uploads/{prep_filename}",
        pdp_area_sq_cm=cv_info["pdp_area_sq_cm"],
        declarations=extraction.declarations,
        scorecard=scorecard
    )
    return resp

@router.put("/{inspection_id}/declarations/{decl_id}", response_model=InspectionDetailResponse)
async def update_declaration(
    inspection_id: str,
    decl_id: str,
    dto: DeclarationUpdateDTO
):
    updated = InspectionRepository.update_declaration(
        inspection_id=inspection_id,
        decl_id=decl_id,
        update_dto=dto
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Inspection or declaration not found")
    return updated

@router.post("/{inspection_id}/review", response_model=InspectionDetailResponse)
async def submit_inspector_review(
    inspection_id: str,
    review: InspectorReviewRequest
):
    updated = InspectionRepository.apply_inspector_review(
        inspection_id=inspection_id,
        review=review
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return updated

@router.get("/{inspection_id}/report.pdf")
async def download_report_pdf(inspection_id: str):
    insp = InspectionRepository.get_inspection_by_id(inspection_id)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    pdf_path = ReportService.generate_inspection_pdf(insp)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path)
    )
