import uuid
from typing import List, Optional
from backend.app.schemas.compliance import ComplianceEvaluationResult, RuleCheckResult
from backend.app.schemas.evidence import EvidenceModel, EvidenceListResponse, EvidenceSummary
from backend.app.schemas.ocr import PixelBoundingBox

class EvidenceService:
    """
    Constructs an auditable, grounded trace from Statutory Rule -> Compliance Check -> Extracted Fact -> Image Region.
    Never fabricates bounding boxes.
    """

    @classmethod
    def build_evidence(
        cls,
        inspection_id: str,
        compliance_result: ComplianceEvaluationResult,
        image_id: str = "original_image"
    ) -> EvidenceListResponse:
        evidence_items: List[EvidenceModel] = []

        detected_count = 0
        incorrect_count = 0
        absence_count = 0
        uncertain_count = 0

        for check in compliance_result.checks:
            # Skip purely not-applicable rules in evidence ledger
            if check.status == "NOT_APPLICABLE":
                continue

            ev_id = f"ev_{uuid.uuid4().hex[:10]}"
            ev_ref = check.evidence_reference or {}
            raw_box = ev_ref.get("bounding_box")

            bounding_box: Optional[PixelBoundingBox] = None
            if raw_box and isinstance(raw_box, dict) and raw_box.get("width", 0) > 0 and raw_box.get("height", 0) > 0:
                bounding_box = PixelBoundingBox(**raw_box)

            # 1. Evidence of Absence
            if check.detection_status == "NOT_FOUND":
                absence_count += 1
                evidence_items.append(
                    EvidenceModel(
                        evidence_id=ev_id,
                        inspection_id=inspection_id,
                        rule_id=check.rule_id,
                        type="ABSENCE",
                        image_id=image_id,
                        bounding_box=None,  # NEVER fabricate a bounding box for absence
                        detected_text=None,
                        confidence=check.confidence,
                        explanation=f"Evidence of absence: The mandatory declaration '{check.field}' was verified absent after scanning the package label.",
                        evidence_available=False
                    )
                )

            # 2. Evidence of Detected Incorrect Declaration (Violation with detected text)
            elif check.status == "POTENTIAL_VIOLATION" and check.detection_status == "FOUND":
                incorrect_count += 1
                evidence_items.append(
                    EvidenceModel(
                        evidence_id=ev_id,
                        inspection_id=inspection_id,
                        rule_id=check.rule_id,
                        type="INCORRECT_DECLARATION",
                        image_id=image_id,
                        bounding_box=bounding_box,
                        detected_text=check.extracted_value,
                        confidence=check.confidence,
                        explanation=f"Evidence of non-compliance: Detected text '{check.extracted_value}' violates requirement: {check.reason}",
                        evidence_available=bounding_box is not None
                    )
                )

            # 3. Uncertain Result Requiring Manual Verification
            elif check.status == "MANUAL_REVIEW" or check.detection_status == "UNCLEAR":
                uncertain_count += 1
                has_region = bounding_box is not None
                evidence_items.append(
                    EvidenceModel(
                        evidence_id=ev_id,
                        inspection_id=inspection_id,
                        rule_id=check.rule_id,
                        type="UNCERTAIN",
                        image_id=image_id,
                        bounding_box=bounding_box,
                        detected_text=check.extracted_value,
                        confidence=check.confidence,
                        explanation=(
                            f"Uncertain perception (confidence: {check.confidence:.2f}). Evidence region candidate flagged for manual inspection."
                            if has_region
                            else "Evidence unavailable — manual verification required."
                        ),
                        evidence_available=has_region
                    )
                )

            # 4. Compliant Detected Declaration
            elif check.status == "COMPLIANT" and check.detection_status == "FOUND":
                detected_count += 1
                evidence_items.append(
                    EvidenceModel(
                        evidence_id=ev_id,
                        inspection_id=inspection_id,
                        rule_id=check.rule_id,
                        type="DETECTED_DECLARATION",
                        image_id=image_id,
                        bounding_box=bounding_box,
                        detected_text=check.extracted_value,
                        confidence=check.confidence,
                        explanation=f"Evidence of compliance: Grounded declaration '{check.extracted_value}' satisfies rule requirement.",
                        evidence_available=bounding_box is not None
                    )
                )

        return EvidenceListResponse(
            inspection_id=inspection_id,
            total=len(evidence_items),
            evidence=evidence_items,
            summary=EvidenceSummary(
                detected_count=detected_count,
                incorrect_count=incorrect_count,
                absence_count=absence_count,
                uncertain_count=uncertain_count
            )
        )
