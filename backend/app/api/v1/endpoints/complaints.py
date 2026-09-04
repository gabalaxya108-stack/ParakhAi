from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Body, Query
from pydantic import BaseModel, Field
from backend.app.db.session import SessionLocal
from backend.app.models import Complaint, Inspection, User, AuditLog

router = APIRouter(prefix="/complaints")

class CreateComplaintRequest(BaseModel):
    inspection_id: str = Field(..., description="Associated inspection ID")
    product_name: Optional[str] = Field(None, description="Commodity / Brand Name")
    manufacturer_name: Optional[str] = Field(None, description="Manufacturer or Packer")
    commodity_category: str = Field("packaged_commodity", description="Commodity category")
    statutory_provisions: Optional[str] = Field(None, description="Violated Legal Metrology provisions")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="List of detected non-compliant declarations")
    evidence_summary: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Evidence image crops and bounding boxes")
    enforcement_notes: Optional[str] = Field(None, description="Inspector notes on recommended statutory action")
    inspector_name: str = Field("inspector.demo", description="Submitting inspector")

class ComplaintDTO(BaseModel):
    id: int
    complaint_id: str
    inspection_id: str
    product_name: Optional[str]
    manufacturer_name: Optional[str]
    commodity_category: str
    status: str
    statutory_provisions: Optional[str]
    violations_json: Optional[Any]
    enforcement_notes: Optional[str]
    created_at: str
    updated_at: str

@router.post("", response_model=ComplaintDTO, summary="Register an Official Legal Metrology Complaint")
def create_complaint(payload: CreateComplaintRequest = Body(...)):
    with SessionLocal() as db:
        # Check inspection
        insp = db.query(Inspection).filter(Inspection.inspection_id == payload.inspection_id).first()
        inspector = db.query(User).filter(User.username == payload.inspector_name).first()
        if not inspector:
            inspector = db.query(User).first()

        now = datetime.now(timezone.utc)
        count = db.query(Complaint).count() + 1
        complaint_id = f"CMP-2026-{count:04d}"

        comp = Complaint(
            complaint_id=complaint_id,
            inspection_id=payload.inspection_id,
            product_id=insp.product_id if insp else None,
            inspector_id=inspector.id if inspector else None,
            product_name=payload.product_name or (insp.product.product_name if insp and insp.product else "Packaged Commodity"),
            manufacturer_name=payload.manufacturer_name or (insp.product.manufacturer if insp and insp.product else None),
            commodity_category=payload.commodity_category,
            status="PENDING_NOTICE",
            statutory_provisions=payload.statutory_provisions or "Rule 6 of Legal Metrology (Packaged Commodities) Rules, 2011",
            violations_json=payload.violations,
            evidence_summary_json=payload.evidence_summary,
            enforcement_notes=payload.enforcement_notes or "Forwarded to Enforcement Queue for statutory notice issuance.",
            created_at=now,
            updated_at=now
        )
        db.add(comp)

        # Update inspection status
        if insp:
            insp.review_status = "COMPLAINT_SUBMITTED"
            insp.updated_at = now

        # Record audit log
        audit = AuditLog(
            inspection_id=insp.id if insp else None,
            user_id=inspector.id if inspector else None,
            action="COMPLAINT_REGISTERED",
            entity_type="Complaint",
            entity_id=complaint_id,
            change_details_json={
                "complaint_id": complaint_id,
                "inspection_id": payload.inspection_id,
                "status": "PENDING_NOTICE",
                "violations_count": len(payload.violations)
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(comp)

        return ComplaintDTO(
            id=comp.id,
            complaint_id=comp.complaint_id,
            inspection_id=comp.inspection_id,
            product_name=comp.product_name,
            manufacturer_name=comp.manufacturer_name,
            commodity_category=comp.commodity_category,
            status=comp.status,
            statutory_provisions=comp.statutory_provisions,
            violations_json=comp.violations_json,
            enforcement_notes=comp.enforcement_notes,
            created_at=comp.created_at.isoformat(),
            updated_at=comp.updated_at.isoformat()
        )

@router.get("", response_model=List[ComplaintDTO], summary="List All Complaints in Enforcement Queue")
def list_complaints(
    status_filter: Optional[str] = Query(None, description="Filter by status: PENDING_NOTICE, NOTICE_ISSUED, CLOSED"),
    limit: int = Query(50, ge=1, le=200)
):
    with SessionLocal() as db:
        q = db.query(Complaint).order_by(Complaint.created_at.desc())
        if status_filter:
            q = q.filter(Complaint.status == status_filter.upper())
        items = q.limit(limit).all()

        return [
            ComplaintDTO(
                id=c.id,
                complaint_id=c.complaint_id,
                inspection_id=c.inspection_id,
                product_name=c.product_name,
                manufacturer_name=c.manufacturer_name,
                commodity_category=c.commodity_category,
                status=c.status,
                statutory_provisions=c.statutory_provisions,
                violations_json=c.violations_json,
                enforcement_notes=c.enforcement_notes,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat()
            )
            for c in items
        ]

@router.patch("/{complaint_id}/status", response_model=ComplaintDTO, summary="Update Complaint Enforcement Status")
def update_complaint_status(
    complaint_id: str,
    new_status: str = Body(..., embed=True, description="PENDING_NOTICE, NOTICE_ISSUED, HEARING_SCHEDULED, CLOSED"),
    notes: Optional[str] = Body(None, embed=True)
):
    with SessionLocal() as db:
        comp = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

        comp.status = new_status.upper()
        if notes:
            date_str = datetime.now(timezone.utc).strftime('%d-%b-%Y')
            comp.enforcement_notes = (comp.enforcement_notes or "") + chr(10) + f"[{date_str}]: {notes}"
        comp.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(comp)

        return ComplaintDTO(
            id=comp.id,
            complaint_id=comp.complaint_id,
            inspection_id=comp.inspection_id,
            product_name=comp.product_name,
            manufacturer_name=comp.manufacturer_name,
            commodity_category=comp.commodity_category,
            status=comp.status,
            statutory_provisions=comp.statutory_provisions,
            violations_json=comp.violations_json,
            enforcement_notes=comp.enforcement_notes,
            created_at=comp.created_at.isoformat(),
            updated_at=comp.updated_at.isoformat()
        )
