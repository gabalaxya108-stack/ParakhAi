from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.db.session import SessionLocal
from backend.app.models import (
    Inspection, Product, Declaration, ComplianceCheck,
    Complaint, AuditLog, User, Evidence
)

router = APIRouter(prefix="/system")

@router.get("/database-tables", summary="Safe Read-Only PostgreSQL Live Records for System Monitor")
def get_database_tables(
    table: str = Query("inspections", description="inspections | products | declarations | compliance_checks | complaints | audit_logs"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=100)
):
    with SessionLocal() as db:
        data = []
        schema_fields = []

        if table == "inspections":
            schema_fields = ["id", "inspection_id", "product_name", "category", "overall_status", "risk_score", "review_status", "created_at"]
            q = db.query(Inspection).order_by(Inspection.created_at.desc())
            if search:
                s = f"%{search.strip()}%"
                q = q.filter(Inspection.inspection_id.ilike(s) | Inspection.overall_status.ilike(s))
            rows = q.limit(limit).all()
            for r in rows:
                p_name = r.product.product_name if r.product else "Unknown Commodity"
                p_cat = r.product.category if r.product else "packaged_commodity"
                data.append({
                    "id": r.id,
                    "inspection_id": r.inspection_id,
                    "product_name": p_name,
                    "category": p_cat,
                    "overall_status": r.overall_status,
                    "risk_score": r.risk_score,
                    "review_status": r.review_status,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })

        elif table == "products":
            schema_fields = ["id", "product_name", "category", "manufacturer", "packer", "country_of_origin", "created_at"]
            q = db.query(Product).order_by(Product.created_at.desc())
            if search:
                s = f"%{search.strip()}%"
                q = q.filter(Product.product_name.ilike(s) | Product.manufacturer.ilike(s))
            rows = q.limit(limit).all()
            for r in rows:
                data.append({
                    "id": r.id,
                    "product_name": r.product_name,
                    "category": r.category,
                    "manufacturer": r.manufacturer,
                    "packer": r.packer,
                    "country_of_origin": r.country_of_origin,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })

        elif table == "declarations":
            schema_fields = ["id", "inspection_id", "field_name", "value", "confidence", "source", "created_at"]
            q = db.query(Declaration).order_by(Declaration.created_at.desc())
            if search:
                s = f"%{search.strip()}%"
                q = q.filter(Declaration.field_name.ilike(s) | Declaration.value.ilike(s))
            rows = q.limit(limit).all()
            for r in rows:
                insp_id = r.inspection.inspection_id if r.inspection else str(r.inspection_id)
                data.append({
                    "id": r.id,
                    "inspection_id": insp_id,
                    "field_name": r.field_name,
                    "value": r.value,
                    "confidence": round(float(r.confidence or 0.0), 2),
                    "source": r.source,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })

        elif table == "compliance_checks":
            schema_fields = ["id", "inspection_id", "rule_id", "field", "extracted_value", "status", "severity", "confidence"]
            q = db.query(ComplianceCheck).order_by(ComplianceCheck.created_at.desc())
            if search:
                s = f"%{search.strip()}%"
                q = q.filter(ComplianceCheck.rule_id.ilike(s) | ComplianceCheck.field.ilike(s) | ComplianceCheck.status.ilike(s))
            rows = q.limit(limit).all()
            for r in rows:
                insp_id = r.inspection.inspection_id if r.inspection else str(r.inspection_id)
                data.append({
                    "id": r.id,
                    "inspection_id": insp_id,
                    "rule_id": r.rule_id,
                    "field": r.field,
                    "extracted_value": r.extracted_value,
                    "status": r.status,
                    "severity": r.severity,
                    "confidence": round(float(r.confidence or 0.0), 2)
                })

        elif table == "complaints":
            schema_fields = ["id", "complaint_id", "inspection_id", "product_name", "manufacturer_name", "status", "statutory_provisions", "created_at"]
            q = db.query(Complaint).order_by(Complaint.created_at.desc())
            if search:
                s = f"%{search.strip()}%"
                q = q.filter(Complaint.complaint_id.ilike(s) | Complaint.product_name.ilike(s) | Complaint.status.ilike(s))
            rows = q.limit(limit).all()
            for r in rows:
                data.append({
                    "id": r.id,
                    "complaint_id": r.complaint_id,
                    "inspection_id": r.inspection_id,
                    "product_name": r.product_name,
                    "manufacturer_name": r.manufacturer_name,
                    "status": r.status,
                    "statutory_provisions": r.statutory_provisions,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })

        elif table == "audit_logs":
            schema_fields = ["id", "action", "entity_type", "entity_id", "user", "change_details", "timestamp"]
            q = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
            if search:
                s = f"%{search.strip()}%"
                q = q.filter(AuditLog.action.ilike(s) | AuditLog.entity_id.ilike(s))
            rows = q.limit(limit).all()
            for r in rows:
                user_name = r.user.username if r.user else "system"
                data.append({
                    "id": r.id,
                    "action": r.action,
                    "entity_type": r.entity_type,
                    "entity_id": r.entity_id,
                    "user": user_name,
                    "change_details": r.change_details_json,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None
                })

        else:
            raise HTTPException(status_code=400, detail=f"Unknown table '{table}'")

        # Table statistics
        stats = {
            "inspections": db.query(Inspection).count(),
            "products": db.query(Product).count(),
            "declarations": db.query(Declaration).count(),
            "compliance_checks": db.query(ComplianceCheck).count(),
            "complaints": db.query(Complaint).count(),
            "audit_logs": db.query(AuditLog).count()
        }

        return {
            "table": table,
            "total_rows": len(data),
            "schema_fields": schema_fields,
            "rows": data,
            "table_statistics": stats
        }
