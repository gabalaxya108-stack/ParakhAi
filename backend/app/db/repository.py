import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.schemas.inspection import (
    InspectionDetailResponse,
    InspectionSummaryDTO,
    InspectionCreateRequest,
    DeclarationUpdateDTO,
    InspectorReviewRequest
)
from backend.app.schemas.extraction import ExtractedDeclarationDTO, DeclarationType
from backend.app.schemas.rules import (
    ComplianceScorecard,
    RuleEvaluationResult,
    ComplianceStatus,
    RuleSeverity
)
from backend.app.schemas.common import BoundingBox

DB_PATH = os.path.join(os.getcwd(), "legal_metrology.db")

class InspectionRepository:
    @classmethod
    def get_connection(cls):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def initialize_db(cls):
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    id TEXT PRIMARY KEY,
                    inspection_number TEXT UNIQUE,
                    commodity_name TEXT,
                    commodity_category TEXT,
                    brand_name TEXT,
                    batch_number TEXT,
                    image_url TEXT,
                    preprocessed_image_url TEXT,
                    pdp_area_sq_cm REAL,
                    status TEXT,
                    overall_compliance TEXT,
                    inspector_name TEXT,
                    inspector_notes TEXT,
                    inspector_signature TEXT,
                    declarations_json TEXT,
                    scorecard_json TEXT,
                    created_at TEXT,
                    reviewed_at TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    inspection_id TEXT,
                    action TEXT,
                    performed_by TEXT,
                    details_json TEXT,
                    timestamp TEXT
                );
            """)
            conn.commit()

    @classmethod
    def create_inspection(
        cls,
        req: InspectionCreateRequest,
        image_url: str,
        preprocessed_image_url: Optional[str],
        pdp_area_sq_cm: float,
        declarations: List[ExtractedDeclarationDTO],
        scorecard: ComplianceScorecard
    ) -> InspectionDetailResponse:
        insp_id = str(uuid.uuid4())
        # Generate official-looking inspection number: LM-2026-XXXXX
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM inspections")
            count = cur.fetchone()[0] + 1
            insp_num = f"LM-2026-{10000 + count}"

            now_iso = datetime.now().isoformat()
            decl_json = json.dumps([d.model_dump() for d in declarations])
            score_json = json.dumps(scorecard.model_dump())

            cur.execute("""
                INSERT INTO inspections (
                    id, inspection_number, commodity_name, commodity_category,
                    brand_name, batch_number, image_url, preprocessed_image_url,
                    pdp_area_sq_cm, status, overall_compliance, inspector_name,
                    declarations_json, scorecard_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                insp_id, insp_num, req.commodity_name, req.commodity_category,
                req.brand_name, req.batch_number, image_url, preprocessed_image_url,
                pdp_area_sq_cm, "PENDING_REVIEW", scorecard.overall_status.value,
                req.inspector_name, decl_json, score_json, now_iso
            ))

            # Add audit log
            cur.execute("""
                INSERT INTO audit_logs (id, inspection_id, action, performed_by, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), insp_id, "AI_INSPECTION_CREATED",
                req.inspector_name, json.dumps({"overall_compliance": scorecard.overall_status.value}),
                now_iso
            ))
            conn.commit()

        return cls.get_inspection_by_id(insp_id)

    @classmethod
    def get_inspection_by_id(cls, inspection_id: str) -> Optional[InspectionDetailResponse]:
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,))
            row = cur.fetchone()
            if not row:
                return None

            decls = [ExtractedDeclarationDTO(**d) for d in json.loads(row["declarations_json"] or "[]")]
            scorecard = ComplianceScorecard(**json.loads(row["scorecard_json"] or "{}"))

            return InspectionDetailResponse(
                id=row["id"],
                inspection_number=row["inspection_number"],
                commodity_name=row["commodity_name"] or "Unnamed Commodity",
                commodity_category=row["commodity_category"] or "General",
                brand_name=row["brand_name"],
                batch_number=row["batch_number"],
                image_url=row["image_url"],
                preprocessed_image_url=row["preprocessed_image_url"],
                pdp_area_sq_cm=row["pdp_area_sq_cm"],
                status=row["status"],
                overall_compliance=ComplianceStatus(row["overall_compliance"]),
                inspector_name=row["inspector_name"],
                inspector_notes=row["inspector_notes"],
                inspector_signature=row["inspector_signature"],
                declarations=decls,
                compliance_scorecard=scorecard,
                created_at=row["created_at"],
                reviewed_at=row["reviewed_at"]
            )

    @classmethod
    def list_inspections(
        cls,
        status_filter: Optional[str] = None,
        compliance_filter: Optional[str] = None
    ) -> List[InspectionSummaryDTO]:
        with cls.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM inspections ORDER BY created_at DESC"
            cur.execute(query)
            rows = cur.fetchall()

            summaries = []
            for r in rows:
                if status_filter and r["status"] != status_filter:
                    continue
                if compliance_filter and r["overall_compliance"] != compliance_filter:
                    continue

                score = json.loads(r["scorecard_json"] or "{}")
                failed = score.get("failed_count", 0)

                summaries.append(
                    InspectionSummaryDTO(
                        id=r["id"],
                        inspection_number=r["inspection_number"],
                        commodity_name=r["commodity_name"] or "General Package",
                        brand_name=r["brand_name"],
                        commodity_category=r["commodity_category"] or "Food",
                        status=r["status"],
                        overall_compliance=ComplianceStatus(r["overall_compliance"]),
                        created_at=r["created_at"],
                        image_url=r["image_url"],
                        violations_count=failed
                    )
                )
            return summaries

    @classmethod
    def update_declaration(
        cls,
        inspection_id: str,
        decl_id: str,
        update_dto: DeclarationUpdateDTO,
        editor_name: str = "Inspector M. Sharma"
    ) -> Optional[InspectionDetailResponse]:
        inspection = cls.get_inspection_by_id(inspection_id)
        if not inspection:
            return None

        # Update specific declaration
        found = False
        for d in inspection.declarations:
            if d.id == decl_id:
                found = True
                if update_dto.raw_text is not None:
                    d.raw_text = update_dto.raw_text
                if update_dto.normalized_value is not None:
                    d.normalized_value = update_dto.normalized_value
                if update_dto.parsed_attributes is not None:
                    d.parsed_attributes = update_dto.parsed_attributes
                if update_dto.bounding_box is not None:
                    d.bounding_box = update_dto.bounding_box
                d.is_manually_edited = True
                d.edited_by = editor_name
                d.notes = update_dto.notes
                break

        if not found:
            return None

        # Re-evaluate deterministic rules with updated declarations
        from backend.app.services.rule_engine.engine import LegalMetrologyRuleEngine
        new_scorecard = LegalMetrologyRuleEngine.evaluate(
            declarations=inspection.declarations,
            pdp_area_sq_cm=inspection.pdp_area_sq_cm,
            commodity_category=inspection.commodity_category
        )

        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE inspections
                SET declarations_json = ?, scorecard_json = ?, overall_compliance = ?
                WHERE id = ?;
            """, (
                json.dumps([d.model_dump() for d in inspection.declarations]),
                json.dumps(new_scorecard.model_dump()),
                new_scorecard.overall_status.value,
                inspection_id
            ))
            # Log audit trail
            cur.execute("""
                INSERT INTO audit_logs (id, inspection_id, action, performed_by, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), inspection_id, "DECLARATION_EDITED",
                editor_name, json.dumps({"decl_id": decl_id, "new_raw": update_dto.raw_text}),
                datetime.now().isoformat()
            ))
            conn.commit()

        return cls.get_inspection_by_id(inspection_id)

    @classmethod
    def apply_inspector_review(
        cls,
        inspection_id: str,
        review: InspectorReviewRequest
    ) -> Optional[InspectionDetailResponse]:
        inspection = cls.get_inspection_by_id(inspection_id)
        if not inspection:
            return None

        # Build overrides map
        overrides_map = {}
        if review.overrides:
            for ov in review.overrides:
                overrides_map[ov.rule_id] = {
                    "override_verdict": ov.override_verdict,
                    "override_reason": ov.override_reason,
                    "overridden_by": ov.overridden_by
                }

        from backend.app.services.rule_engine.engine import LegalMetrologyRuleEngine
        updated_scorecard = LegalMetrologyRuleEngine.evaluate(
            declarations=inspection.declarations,
            pdp_area_sq_cm=inspection.pdp_area_sq_cm,
            commodity_category=inspection.commodity_category,
            overrides=overrides_map
        )

        now_iso = datetime.now().isoformat()
        status_label = "COMPLIANCE_APPROVED" if review.final_verdict == ComplianceStatus.PASS else "NOTICE_ISSUED"

        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE inspections
                SET status = ?, overall_compliance = ?, inspector_notes = ?,
                    inspector_signature = ?, scorecard_json = ?, reviewed_at = ?
                WHERE id = ?;
            """, (
                status_label,
                review.final_verdict.value,
                review.inspector_notes,
                review.inspector_signature,
                json.dumps(updated_scorecard.model_dump()),
                now_iso,
                inspection_id
            ))

            cur.execute("""
                INSERT INTO audit_logs (id, inspection_id, action, performed_by, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), inspection_id, "REVIEW_FINALIZED",
                inspection.inspector_name,
                json.dumps({"final_verdict": review.final_verdict.value, "notes": review.inspector_notes}),
                now_iso
            ))
            conn.commit()

        return cls.get_inspection_by_id(inspection_id)

    @classmethod
    def get_analytics_summary(cls) -> Dict[str, Any]:
        with cls.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM inspections")
            total_inspections = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM inspections WHERE overall_compliance = 'PASS'")
            total_passed = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM inspections WHERE overall_compliance = 'FAIL'")
            total_failed = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM inspections WHERE status = 'PENDING_REVIEW'")
            pending_reviews = cur.fetchone()[0]

            compliance_rate = round((total_passed / total_inspections * 100), 1) if total_inspections > 0 else 0.0

            # Violation breakdown by rule
            cur.execute("SELECT scorecard_json FROM inspections")
            rows = cur.fetchall()

            rule_counts: Dict[str, int] = {}
            for r in rows:
                sc = json.loads(r[0] or "{}")
                for item in sc.get("results", []):
                    eff_stat = item.get("override_verdict") or item.get("status")
                    if eff_stat == "FAIL":
                        rid = item.get("rule_id", "Unknown")
                        rule_counts[rid] = rule_counts.get(rid, 0) + 1

            # Format top violations
            rule_labels = {
                "LMR-R06-01": "Manufacturer & Packer Details",
                "LMR-R06-02": "Generic Commodity Name on PDP",
                "LMR-R06-03": "Net Quantity SI Units (Illegal 'gms')",
                "LMR-R06-04": "Month & Year of Mfg / Packing",
                "LMR-R06-05": "MRP Format & All Taxes Phrase",
                "LMR-R06-06": "Unit Sale Price (USP) Missing/Mismatch",
                "LMR-R06-07": "Consumer Care & Helpline",
                "LMR-R06-08": "Country of Origin Declaration",
                "LMR-SCH-02": "Schedule II Min Font Height vs PDP"
            }

            top_violations = [
                {"rule_id": k, "label": rule_labels.get(k, k), "count": v}
                for k, v in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            return {
                "total_inspections": total_inspections,
                "compliant_count": total_passed,
                "violation_count": total_failed,
                "pending_review_count": pending_reviews,
                "compliance_rate_pct": compliance_rate,
                "top_violations": top_violations
            }
