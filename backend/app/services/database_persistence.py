import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.db.session import SessionLocal
from backend.app.models import (
    User, Product, RuleVersion, Rule,
    Inspection, Image, OCRResult, Declaration,
    ComplianceCheck, Violation, Evidence,
    InspectionReview, AuditLog
)
from backend.app.core.logging import get_logger

logger = get_logger("services.database_persistence")

class DatabasePersistenceService:
    """
    Manages complete, relational PostgreSQL persistence for inspections,
    products, OCR, declarations, compliance checks, violations, evidence, and audit logs.
    """

    @classmethod
    def get_or_create_default_inspector(cls, db: Session) -> User:
        user = db.query(User).filter(User.username == "inspector_lm").first()
        if not user:
            user = User(
                username="inspector_lm",
                email="inspector@legalmetrology.gov.in",
                full_name="Inspector General of Legal Metrology",
                role="INSPECTOR"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @classmethod
    def persist_inspection_upload(
        cls,
        inspection_id: str,
        filename: str,
        mime_type: str,
        file_size: int,
        storage_key: str,
        public_url: str,
        client_ip: Optional[str] = None
    ) -> Inspection:
        with SessionLocal() as db:
            inspector = cls.get_or_create_default_inspector(db)

            # Check if inspection exists
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                inspection = Inspection(
                    inspection_id=inspection_id,
                    user_id=inspector.id,
                    status="UPLOADED",
                    overall_status="NOT_EVALUATED",
                    risk_score=0,
                    model_provider_version="vision-ocr-v1",
                    rule_version="2026.1",
                    review_status="PENDING"
                )
                db.add(inspection)
                db.flush()

                # Add Image record
                image = Image(
                    inspection_id=inspection.id,
                    file_path=storage_key,
                    file_url=public_url,
                    filename=filename,
                    mime_type=mime_type,
                    file_size=file_size
                )
                db.add(image)

                # Add Audit Log
                audit = AuditLog(
                    inspection_id=inspection.id,
                    user_id=inspector.id,
                    action="IMAGE_UPLOADED",
                    entity_type="Inspection",
                    entity_id=inspection_id,
                    change_details_json={"filename": filename, "file_size": file_size},
                    ip_address=client_ip
                )
                db.add(audit)

                db.commit()
                db.refresh(inspection)
            return inspection

    @classmethod
    def persist_ocr_result(
        cls,
        inspection_id: str,
        ocr_data: Dict[str, Any]
    ) -> None:
        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                return

            image = db.query(Image).filter(Image.inspection_id == inspection.id).first()
            if image and "image_width" in ocr_data and "image_height" in ocr_data:
                image.width = ocr_data.get("image_width")
                image.height = ocr_data.get("image_height")

            # Remove old OCR record if exists
            db.query(OCRResult).filter(OCRResult.inspection_id == inspection.id).delete()

            ocr_record = OCRResult(
                inspection_id=inspection.id,
                image_id=image.id if image else None,
                provider=ocr_data.get("provider", "mock"),
                raw_text=ocr_data.get("raw_text"),
                total_blocks=ocr_data.get("total_blocks", 0),
                processing_time_ms=ocr_data.get("processing_time_ms", 0.0),
                blocks_json=ocr_data.get("blocks", [])
            )
            db.add(ocr_record)

            inspection.status = "OCR_COMPLETED"
            inspection.updated_at = datetime.now(timezone.utc)

            audit = AuditLog(
                inspection_id=inspection.id,
                user_id=inspection.user_id,
                action="OCR_PROCESSED",
                entity_type="OCRResult",
                entity_id=inspection_id,
                change_details_json={"provider": ocr_data.get("provider"), "blocks": ocr_data.get("total_blocks")}
            )
            db.add(audit)
            db.commit()

    @classmethod
    def persist_declarations(
        cls,
        inspection_id: str,
        extraction_data: Dict[str, Any]
    ) -> None:
        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                return

            fields = extraction_data.get("fields", {})
            prod_name = fields.get("product_name", {}).get("value") or "Unspecified Commodity"
            mfr = fields.get("manufacturer", {}).get("value")
            packer = fields.get("packer", {}).get("value")
            importer = fields.get("importer", {}).get("value")
            origin = fields.get("country_of_origin", {}).get("value")

            # Upsert Product
            product = None
            if inspection.product_id:
                product = db.query(Product).filter(Product.id == inspection.product_id).first()
            if not product:
                product = Product(
                    product_name=prod_name,
                    category="packaged_commodity",
                    manufacturer=mfr,
                    packer=packer,
                    importer=importer,
                    country_of_origin=origin
                )
                db.add(product)
                db.flush()
                inspection.product_id = product.id
            else:
                product.product_name = prod_name
                product.manufacturer = mfr
                product.packer = packer
                product.importer = importer
                product.country_of_origin = origin

            # Re-sync declarations table
            db.query(Declaration).filter(Declaration.inspection_id == inspection.id).delete()
            for field_key, f_data in fields.items():
                decl = Declaration(
                    inspection_id=inspection.id,
                    field_name=field_key,
                    value=f_data.get("value"),
                    confidence=float(f_data.get("confidence", 0.0)),
                    source=f_data.get("source", "ocr"),
                    bounding_box_json=f_data.get("bounding_box")
                )
                db.add(decl)

            inspection.status = "EXTRACTION_COMPLETED"
            inspection.model_provider_version = extraction_data.get("provider", "mock-extraction")
            inspection.updated_at = datetime.now(timezone.utc)

            audit = AuditLog(
                inspection_id=inspection.id,
                user_id=inspection.user_id,
                action="EXTRACTION_COMPLETED",
                entity_type="Declaration",
                entity_id=inspection_id,
                change_details_json={"extracted": extraction_data.get("extracted_fields_count"), "missing": extraction_data.get("missing_fields_count")}
            )
            db.add(audit)
            db.commit()

    @classmethod
    def persist_compliance_and_evidence(
        cls,
        inspection_id: str,
        compliance_data: Dict[str, Any],
        evidence_data: Optional[Dict[str, Any]] = None
    ) -> None:
        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                return

            inspection.overall_status = compliance_data.get("overall_status", "NOT_EVALUATED")
            inspection.risk_score = compliance_data.get("risk_score", 0)
            inspection.rule_version = compliance_data.get("rule_version", "2026.1")
            inspection.status = "EVALUATED"
            inspection.updated_at = datetime.now(timezone.utc)

            # Re-sync compliance checks & violations
            db.query(Violation).filter(Violation.inspection_id == inspection.id).delete()
            db.query(Evidence).filter(Evidence.inspection_id == inspection.id).delete()
            db.query(ComplianceCheck).filter(ComplianceCheck.inspection_id == inspection.id).delete()

            check_map = {}
            for chk in compliance_data.get("checks", []):
                check_obj = ComplianceCheck(
                    inspection_id=inspection.id,
                    rule_id=chk.get("rule_id"),
                    field=chk.get("field"),
                    extracted_value=chk.get("extracted_value"),
                    detection_status=chk.get("detection_status"),
                    status=chk.get("status"),
                    reason=chk.get("reason"),
                    severity=chk.get("severity"),
                    confidence=float(chk.get("confidence", 0.0)),
                    evidence_reference_json=chk.get("evidence_reference")
                )
                db.add(check_obj)
                db.flush()
                check_map[chk.get("rule_id")] = check_obj.id

                # If violation, create violation record
                if chk.get("status") == "POTENTIAL_VIOLATION":
                    v_type = "MISSING_DECLARATION" if chk.get("detection_status") == "NOT_FOUND" else "NON_COMPLIANT_DECLARATION"
                    viol = Violation(
                        inspection_id=inspection.id,
                        check_id=check_obj.id,
                        rule_id=chk.get("rule_id"),
                        field=chk.get("field"),
                        violation_type=v_type,
                        severity=chk.get("severity"),
                        description=chk.get("reason")
                    )
                    db.add(viol)

            # Persist Evidence items
            if evidence_data and "evidence" in evidence_data:
                for ev in evidence_data.get("evidence", []):
                    ev_obj = Evidence(
                        evidence_id=ev.get("evidence_id"),
                        inspection_id=inspection.id,
                        check_id=check_map.get(ev.get("rule_id")),
                        rule_id=ev.get("rule_id"),
                        type=ev.get("type"),
                        image_id=ev.get("image_id", "original"),
                        bounding_box_json=ev.get("bounding_box"),
                        detected_text=ev.get("detected_text"),
                        confidence=float(ev.get("confidence", 0.0)),
                        explanation=ev.get("explanation"),
                        evidence_available=bool(ev.get("evidence_available", False))
                    )
                    db.add(ev_obj)

            # Default InspectionReview if none exists
            rev = db.query(InspectionReview).filter(InspectionReview.inspection_id == inspection.id).first()
            if not rev:
                rev = InspectionReview(
                    inspection_id=inspection.id,
                    reviewer_id=inspection.user_id,
                    review_status="PENDING",
                    notes="Automated deterministic evaluation completed. Ready for inspector confirmation."
                )
                db.add(rev)

            audit = AuditLog(
                inspection_id=inspection.id,
                user_id=inspection.user_id,
                action="COMPLIANCE_EVALUATED",
                entity_type="ComplianceEvaluation",
                entity_id=inspection_id,
                change_details_json={
                    "status": inspection.overall_status,
                    "risk_score": inspection.risk_score,
                    "violations": len(compliance_data.get("violations", []))
                }
            )
            db.add(audit)
            db.commit()

    @classmethod
    def get_complete_inspection_dossier(cls, inspection_id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                return None

            inspector_user = db.query(User).filter(User.id == inspection.user_id).first()
            product = db.query(Product).filter(Product.id == inspection.product_id).first()
            image = db.query(Image).filter(Image.inspection_id == inspection.id).first()
            ocr = db.query(OCRResult).filter(OCRResult.inspection_id == inspection.id).first()
            declarations = db.query(Declaration).filter(Declaration.inspection_id == inspection.id).all()
            checks = db.query(ComplianceCheck).filter(ComplianceCheck.inspection_id == inspection.id).all()
            violations = db.query(Violation).filter(Violation.inspection_id == inspection.id).all()
            evidence = db.query(Evidence).filter(Evidence.inspection_id == inspection.id).all()
            review = db.query(InspectionReview).filter(InspectionReview.inspection_id == inspection.id).first()

            # Assemble clean declarations container map
            decl_map = {}
            for d in declarations:
                decl_map[d.field_name] = {
                    "field": d.field_name,
                    "value": d.value,
                    "confidence": d.confidence,
                    "source": d.source,
                    "bounding_box": d.bounding_box_json
                }

            checks_list = [
                {
                    "rule_id": c.rule_id,
                    "requirement": "",  # populated from rule
                    "field": c.field,
                    "extracted_value": c.extracted_value,
                    "detection_status": c.detection_status,
                    "status": c.status,
                    "reason": c.reason,
                    "severity": c.severity,
                    "confidence": c.confidence,
                    "evidence_reference": c.evidence_reference_json
                }
                for c in checks
            ]

            violations_list = [
                {
                    "rule_id": v.rule_id,
                    "field": v.field,
                    "violation_type": v.violation_type,
                    "severity": v.severity,
                    "description": v.description
                }
                for v in violations
            ]

            evidence_list = [
                {
                    "evidence_id": e.evidence_id,
                    "rule_id": e.rule_id,
                    "type": e.type,
                    "image_id": e.image_id,
                    "bounding_box": e.bounding_box_json,
                    "detected_text": e.detected_text,
                    "confidence": e.confidence,
                    "explanation": e.explanation,
                    "evidence_available": e.evidence_available
                }
                for e in evidence
            ]

            from backend.app.repositories.inspection_repository import InspectionRepository
            from backend.app.services.compliance.canonical_requirements import CanonicalAggregator

            repo_insp = InspectionRepository()
            cached_comp = repo_insp.get_compliance_result(inspection.inspection_id) or {}

            human_reviews = cached_comp.get("human_reviews", {})
            if not human_reviews:
                override_logs = db.query(AuditLog).filter(
                    AuditLog.inspection_id == inspection.id,
                    AuditLog.action == "INSPECTOR_CHECK_OVERRIDE"
                ).all()
                for log in override_logs:
                    details = log.change_details_json or {}
                    cid = details.get("canonical_id")
                    if cid:
                        human_reviews[cid] = details

            canonical_reqs = cached_comp.get("canonical_requirements")
            if not canonical_reqs and checks:
                groups = CanonicalAggregator.aggregate(
                    checks=checks,
                    fields_map=decl_map,
                    human_reviews=human_reviews
                )
                canonical_reqs = [g.model_dump() for g in groups]

            confirmed_count = cached_comp.get("confirmed_violations_count")
            if confirmed_count is None:
                confirmed_count = sum(1 for c in (canonical_reqs or []) if c.get("status") in ["NON_COMPLIANT", "POTENTIAL_VIOLATION"])

            review_count = cached_comp.get("items_needing_review_count")
            if review_count is None:
                review_count = sum(1 for c in (canonical_reqs or []) if c.get("status") in ["NEEDS_REVIEW", "MANUAL_REVIEW"])

            coverage_pct = cached_comp.get("evidence_coverage_percent")
            if coverage_pct is None:
                ev_avail = sum(1 for e in evidence if e.evidence_available)
                coverage_pct = round((ev_avail / len(checks_list) * 100), 1) if checks_list else 100.0

            screening_score = cached_comp.get("screening_priority_score", inspection.risk_score)

            return {
                "inspection_id": inspection.inspection_id,
                "filename": image.filename if image else "original.jpg",
                "image_url": image.file_url if image else "",
                "mime_type": image.mime_type if image else "image/jpeg",
                "file_size": image.file_size if image else 0,
                "created_at": inspection.created_at.isoformat(),
                "updated_at": inspection.updated_at.isoformat(),
                "status": inspection.status,
                "overall_status": inspection.overall_status,
                "risk_score": inspection.risk_score,
                "screening_priority_score": screening_score,
                "confirmed_violations_count": confirmed_count,
                "items_needing_review_count": review_count,
                "evidence_coverage_percent": coverage_pct,
                "canonical_requirements": canonical_reqs or [],
                "human_reviews": human_reviews,
                "model_provider_version": inspection.model_provider_version,
                "rule_version": inspection.rule_version,
                "review_status": review.review_status if review else inspection.review_status,
                "inspector": {
                    "id": inspector_user.id if inspector_user else None,
                    "username": inspector_user.username if inspector_user else "inspector_lm",
                    "full_name": inspector_user.full_name if inspector_user else "Inspector General",
                    "role": inspector_user.role if inspector_user else "INSPECTOR"
                },
                "product": {
                    "id": product.id if product else None,
                    "product_name": product.product_name if product else "Unknown Commodity",
                    "category": product.category if product else "packaged_commodity",
                    "manufacturer": product.manufacturer if product else None,
                    "packer": product.packer if product else None,
                    "importer": product.importer if product else None,
                    "country_of_origin": product.country_of_origin if product else None
                },
                "image": {
                    "filename": image.filename if image else "original.jpg",
                    "file_url": image.file_url if image else "",
                    "mime_type": image.mime_type if image else "image/jpeg",
                    "file_size": image.file_size if image else 0,
                    "width": image.width if image else None,
                    "height": image.height if image else None
                },
                "ocr": {
                    "provider": ocr.provider if ocr else None,
                    "total_blocks": ocr.total_blocks if ocr else 0,
                    "processing_time_ms": ocr.processing_time_ms if ocr else 0.0,
                    "blocks": ocr.blocks_json if ocr else []
                },
                "extracted_declarations": decl_map,
                "compliance_result": {
                    "inspection_id": inspection.inspection_id,
                    "filename": image.filename if image else "original.jpg",
                    "image_url": image.file_url if image else "",
                    "mime_type": image.mime_type if image else "image/jpeg",
                    "file_size": image.file_size if image else 0,
                    "overall_status": inspection.overall_status,
                    "risk_score": inspection.risk_score,
                    "screening_priority_score": screening_score,
                    "confirmed_violations_count": confirmed_count,
                    "items_needing_review_count": review_count,
                    "evidence_coverage_percent": coverage_pct,
                    "canonical_requirements": canonical_reqs or [],
                    "human_reviews": human_reviews,
                    "product_category": product.category if product else "packaged_commodity",
                    "rule_version": inspection.rule_version,
                    "violations": violations_list,
                    "checks": checks_list,
                    "timestamp": inspection.updated_at.isoformat()
                },
                "evidence": evidence_list
            }

    @classmethod
    def list_all_inspections(cls, limit: int = 100) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            inspections = db.query(Inspection).order_by(desc(Inspection.created_at)).limit(limit).all()
            results = []
            for insp in inspections:
                product = db.query(Product).filter(Product.id == insp.product_id).first()
                inspector = db.query(User).filter(User.id == insp.user_id).first()
                image = db.query(Image).filter(Image.inspection_id == insp.id).first()
                review = db.query(InspectionReview).filter(InspectionReview.inspection_id == insp.id).first()
                violations_count = db.query(Violation).filter(Violation.inspection_id == insp.id).count()

                results.append({
                    "inspection_id": insp.inspection_id,
                    "created_at": insp.created_at.isoformat(),
                    "updated_at": insp.updated_at.isoformat(),
                    "status": insp.status,
                    "overall_status": insp.overall_status,
                    "risk_score": insp.risk_score,
                    "model_provider_version": insp.model_provider_version,
                    "rule_version": insp.rule_version,
                    "review_status": review.review_status if review else insp.review_status,
                    "inspector": inspector.username if inspector else "inspector_lm",
                    "product": {
                        "name": product.product_name if product else None,
                        "manufacturer": product.manufacturer if product else None,
                        "category": product.category if product else "packaged_commodity"
                    },
                    "image": {
                        "filename": image.filename if image else None,
                        "url": image.file_url if image else None
                    },
                    "violations_count": violations_count
                })
            return results

    @classmethod
    def submit_inspection_review(
        cls,
        inspection_id: str,
        decision: str,
        comment: Optional[str] = None,
        reviewer_name: str = "inspector_lm",
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                raise ValueError(f"Inspection '{inspection_id}' not found.")

            # Find or create reviewer user
            reviewer = db.query(User).filter(User.username == reviewer_name).first()
            if not reviewer:
                reviewer = cls.get_or_create_default_inspector(db)

            # Preserve AI result: capture immutable values before recording review
            original_ai_status = inspection.overall_status
            original_ai_risk = inspection.risk_score

            # Create InspectionReview record
            now = datetime.now(timezone.utc)
            review = InspectionReview(
                inspection_id=inspection.id,
                reviewer_id=reviewer.id,
                review_status=decision,
                notes=comment,
                decision_timestamp=now
            )
            db.add(review)
            db.flush()

            # Update inspection human review status while STRICTLY preserving original AI screening status
            inspection.review_status = decision
            inspection.updated_at = now

            # Record in immutable AuditLog
            audit = AuditLog(
                inspection_id=inspection.id,
                user_id=reviewer.id,
                action="INSPECTION_REVIEW_SUBMITTED",
                entity_type="InspectionReview",
                entity_id=str(review.id),
                change_details_json={
                    "decision": decision,
                    "comment": comment,
                    "reviewer": reviewer.username,
                    "preserved_original_ai_status": original_ai_status,
                    "preserved_original_ai_risk_score": original_ai_risk
                },
                ip_address=client_ip,
                timestamp=now
            )
            db.add(audit)
            db.commit()

            decision_labels = {
                "CONFIRM_FINDING": "Confirmed Finding",
                "REJECT_FINDING": "Rejected Finding",
                "REQUEST_MANUAL_VERIFICATION": "Requested Manual Verification",
                "MARK_NOT_APPLICABLE": "Marked Not Applicable"
            }

            return {
                "review_id": review.id,
                "inspection_id": inspection.inspection_id,
                "reviewer": reviewer.username,
                "decision": decision,
                "decision_label": decision_labels.get(decision, decision),
                "comment": comment,
                "timestamp": now.isoformat(),
                "original_ai_status": original_ai_status,
                "original_ai_risk_score": original_ai_risk
            }

    @classmethod
    def get_inspection_reviews(cls, inspection_id: str) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                return []

            reviews = (
                db.query(InspectionReview)
                .filter(InspectionReview.inspection_id == inspection.id)
                .order_by(desc(InspectionReview.created_at))
                .all()
            )

            decision_labels = {
                "CONFIRM_FINDING": "Confirmed Finding",
                "REJECT_FINDING": "Rejected Finding",
                "REQUEST_MANUAL_VERIFICATION": "Requested Manual Verification",
                "MARK_NOT_APPLICABLE": "Marked Not Applicable"
            }

            results = []
            for r in reviews:
                reviewer = db.query(User).filter(User.id == r.reviewer_id).first() if r.reviewer_id else None
                results.append({
                    "review_id": r.id,
                    "inspection_id": inspection.inspection_id,
                    "reviewer": reviewer.username if reviewer else "inspector_lm",
                    "decision": r.review_status,
                    "decision_label": decision_labels.get(r.review_status, r.review_status),
                    "comment": r.notes,
                    "timestamp": r.decision_timestamp.isoformat() if r.decision_timestamp else r.created_at.isoformat(),
                    "original_ai_status": inspection.overall_status,
                    "original_ai_risk_score": inspection.risk_score
                })
            return results

    @classmethod
    def record_check_review(
        cls,
        inspection_id: str,
        canonical_id: str,
        decision: str,
        reason: str,
        remarks: Optional[str] = None,
        reviewer_name: str = "INS-DL-4029",
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a human-in-the-loop inspector review on a canonical statutory requirement.
        Preserves original AI preliminary status while recalculating authoritative compliance.
        """
        from backend.app.services.compliance.engine import ComplianceEngine
        from backend.app.repositories.regulatory_repository import RegulatoryRepository
        from backend.app.repositories.inspection_repository import InspectionRepository

        repo_insp = InspectionRepository()
        comp_json = repo_insp.get_compliance_result(inspection_id) or {}
        ext_json = repo_insp.get_extraction_result(inspection_id) or {}

        with SessionLocal() as db:
            inspection = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if not inspection:
                raise ValueError(f"Inspection {inspection_id} not found.")

            reviewer = db.query(User).filter(User.username == reviewer_name).first()
            if not reviewer:
                reviewer = cls.get_or_create_default_inspector(db)

            if not ext_json:
                dossier = cls.get_complete_inspection_dossier(inspection_id) or {}
                ext_json = {"fields": dossier.get("extracted_declarations", {})}

            human_reviews = comp_json.get("human_reviews", {}) if isinstance(comp_json, dict) else {}
            now_iso = datetime.now(timezone.utc).isoformat()

            # Find original status of this canonical requirement
            orig_req_status = "NEEDS_REVIEW"
            for cr in comp_json.get("canonical_requirements", []):
                if cr.get("canonical_id") == canonical_id:
                    orig_req_status = cr.get("status", "NEEDS_REVIEW")
                    break

            human_reviews[canonical_id] = {
                "canonical_id": canonical_id,
                "decision": decision,
                "reason": reason,
                "remarks": remarks,
                "reviewer": reviewer_name,
                "timestamp": now_iso,
                "original_ai_status": orig_req_status
            }

            # Re-evaluate with human reviews mapping
            repo = RegulatoryRepository()
            category = comp_json.get("product_category") or "packaged_commodity"
            rules = repo.get_applicable_rules(category=category, inspection_date=now_iso[:10])

            recalculated = ComplianceEngine.evaluate(
                inspection_id=inspection_id,
                extracted_declarations=ext_json,
                product_category=category,
                applicable_rules=rules,
                rule_version=comp_json.get("rule_version", "2026.1"),
                human_reviews=human_reviews
            )

            updated_comp_dict = recalculated.model_dump()
            repo_insp.save_compliance_result(inspection_id, updated_comp_dict)

            inspection.overall_status = recalculated.overall_status
            inspection.risk_score = recalculated.screening_priority_score
            inspection.review_status = "HUMAN_VERIFIED"
            inspection.updated_at = datetime.now(timezone.utc)

            # Record in immutable AuditLog
            audit = AuditLog(
                inspection_id=inspection.id,
                user_id=reviewer.id,
                action="INSPECTOR_CHECK_OVERRIDE",
                entity_type="CanonicalRequirementReview",
                entity_id=canonical_id,
                change_details_json={
                    "canonical_id": canonical_id,
                    "decision": decision,
                    "reason": reason,
                    "remarks": remarks,
                    "reviewer": reviewer_name,
                    "original_ai_status": orig_req_status,
                    "resulting_overall_status": recalculated.overall_status
                },
                ip_address=client_ip,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(audit)
            db.commit()

            return updated_comp_dict

    @classmethod
    def update_inspection_review_status(cls, inspection_id: str, new_status: str):
        with SessionLocal() as db:
            insp = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            if insp:
                insp.review_status = new_status
                insp.updated_at = datetime.now(timezone.utc)
                db.commit()

    @classmethod
    def create_complaint(
        cls,
        inspection_id: str,
        enforcement_notes: str,
        statutory_provisions: str,
        inspector_name: str = "inspector.demo",
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        from backend.app.models import Complaint, AuditLog
        with SessionLocal() as db:
            insp = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
            inspector = db.query(User).filter(User.username == inspector_name).first()
            if not inspector:
                inspector = cls.get_or_create_default_inspector(db)

            now = datetime.now(timezone.utc)
            count = db.query(Complaint).count() + 1
            complaint_id = f"CMP-2026-{count:04d}"

            # Get violations from compliance check
            violations = db.query(Violation).filter(Violation.inspection_id == insp.id).all() if insp else []
            viol_list = [
                {
                    "rule_id": v.rule_id,
                    "requirement": v.description,
                    "severity": v.severity,
                    "penalty_provision": getattr(v, "penalty_clause", "Section 36(1) of Legal Metrology Act, 2009")
                }
                for v in violations
            ]

            comp = Complaint(
                complaint_id=complaint_id,
                inspection_id=inspection_id,
                product_id=insp.product_id if insp else None,
                inspector_id=inspector.id,
                product_name=insp.product.product_name if insp and insp.product else "Packaged Commodity",
                manufacturer_name=insp.product.manufacturer if insp and insp.product else "Commercial Entity",
                commodity_category=insp.product.category if insp and insp.product else "packaged_commodity",
                status="PENDING_NOTICE",
                statutory_provisions=statutory_provisions,
                violations_json=viol_list,
                enforcement_notes=enforcement_notes,
                created_at=now,
                updated_at=now
            )
            db.add(comp)
            if insp:
                insp.review_status = "COMPLAINT_REGISTERED"
                insp.updated_at = now

            audit = AuditLog(
                inspection_id=insp.id if insp else None,
                user_id=inspector.id,
                action="COMPLAINT_REGISTERED",
                entity_type="Complaint",
                entity_id=complaint_id,
                change_details_json={
                    "complaint_id": complaint_id,
                    "inspection_id": inspection_id,
                    "statutory_provisions": statutory_provisions,
                    "violations_count": len(viol_list),
                    "enforcement_notes": enforcement_notes
                },
                ip_address=client_ip,
                timestamp=now
            )
            db.add(audit)
            db.commit()

            return {
                "complaint_id": complaint_id,
                "inspection_id": inspection_id,
                "status": "PENDING_NOTICE",
                "created_at": now.isoformat()
            }

