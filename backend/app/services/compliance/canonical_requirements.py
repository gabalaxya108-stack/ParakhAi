from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SubCheckItem(BaseModel):
    rule_id: str
    rule_title: str
    section: Optional[str] = 'Rule 6'
    status: str  # COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, NOT_APPLICABLE
    reason: str
    confidence: float
    extracted_value: Optional[str] = None
    severity: str = 'MEDIUM'

class CanonicalRequirementGroup(BaseModel):
    canonical_id: str  # e.g. REQ-MRP, REQ-NET-QTY
    title: str        # e.g. "Maximum Retail Price (MRP)"
    statutory_rule: str # e.g. "Rule 6(1)(e) & 6(11)"
    field: str        # e.g. "mrp"
    status: str       # COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, NOT_APPLICABLE
    extracted_value: Optional[str] = None
    normalized_summary: Optional[Dict[str, Any]] = None
    confidence: float
    overall_reason: str
    sub_checks: List[SubCheckItem] = Field(default_factory=list)
    evidence_crop_url: Optional[str] = None
    human_review: Optional[Dict[str, Any]] = None

CANONICAL_REQUIREMENT_DEFINITIONS = [
    {
        "canonical_id": "REQ-MRP",
        "title": "Maximum Retail Price (MRP)",
        "statutory_rule": "Rule 6(1)(e) & 6(11)",
        "field": "mrp",
        "rule_ids": ["LM-MRP-001", "LM-MRP-002", "LM-USP-001", "LM-ECOM-001", "PCR-R6-001", "PCR-R6-002", "PCR-R6-010", "PCR-R6-011", "LMR-R06-05", "LMR-R06-06"]
    },
    {
        "canonical_id": "REQ-NET-QTY",
        "title": "Net Quantity",
        "statutory_rule": "Rule 6(1)(f) & Schedule II",
        "field": "net_quantity",
        "rule_ids": ["LM-NETQTY-001", "LM-NETQTY-002", "LM-FONT-001", "PCR-R6-003", "PCR-R11-001", "PCR-R9-001", "LMR-R06-03", "LMR-SCH-02"]
    },
    {
        "canonical_id": "REQ-MFD-PACKER",
        "title": "Manufacturer / Packer Details",
        "statutory_rule": "Rule 6(1)(a)",
        "field": "manufacturer",
        "rule_ids": ["LM-MFD-001", "LM-NAME-001", "PCR-R6-004", "PCR-R6-005", "LMR-R06-01", "LMR-R06-02"]
    },
    {
        "canonical_id": "REQ-DATE",
        "title": "Date of Manufacture or Packing",
        "statutory_rule": "Rule 6(1)(d)",
        "field": "manufacturing_date",
        "rule_ids": ["LM-DATE-001", "PCR-R6-006", "LMR-R06-04"]
    },
    {
        "canonical_id": "REQ-CONSUMER-CARE",
        "title": "Consumer Care Redressal",
        "statutory_rule": "Rule 6(1)(da)",
        "field": "consumer_care",
        "rule_ids": ["LM-CARE-001", "PCR-R6-007", "LMR-R06-07"]
    },
    {
        "canonical_id": "REQ-ORIGIN",
        "title": "Country of Origin",
        "statutory_rule": "Rule 6(1)(g)",
        "field": "country_of_origin",
        "rule_ids": ["LM-ORIGIN-001", "PCR-R6-008", "LMR-R06-08"]
    },
    {
        "canonical_id": "REQ-BATCH",
        "title": "Batch or Lot Number",
        "statutory_rule": "Rule 6(1)(q)",
        "field": "batch_or_lot_number",
        "rule_ids": ["LM-LOT-001", "PCR-R6-009"]
    },
    {
        "canonical_id": "REQ-EXPIRY",
        "title": "Best Before / Use By Date",
        "statutory_rule": "Rule 6(1)(g) & FSSAI Regulations",
        "field": "expiry_date",
        "rule_ids": ["LM-EXPIRY-001"]
    },
    {
        "canonical_id": "REQ-FSSAI",
        "title": "FSSAI License Number",
        "statutory_rule": "FSSAI Act 2006 / Rule 6 Cross-Reference",
        "field": "fssai_license",
        "rule_ids": ["LM-FSSAI-001"]
    },
    {
        "canonical_id": "REQ-VEGMARK",
        "title": "Veg / Non-Veg Marking",
        "statutory_rule": "FSSAI Reg. 2.2.2 / Rule 6 Cross-Reference",
        "field": "veg_nonveg_mark",
        "rule_ids": ["LM-VEGMARK-001"]
    },
    {
        "canonical_id": "REQ-INGREDIENTS",
        "title": "List of Ingredients",
        "statutory_rule": "FSSAI Reg. 2.2.1 / Rule 6 Cross-Reference",
        "field": "ingredients_list",
        "rule_ids": ["LM-INGRED-001"]
    },
    {
        "canonical_id": "REQ-NUTRITION",
        "title": "Nutritional Information",
        "statutory_rule": "FSSAI Reg. 2.2.2 / Rule 6 Cross-Reference",
        "field": "nutritional_info",
        "rule_ids": ["LM-NUTRI-001"]
    }
]

class CanonicalAggregator:
    """
    Groups granular statutory checks into Canonical Mandatory Requirements (up to 12 groups).
    Eliminates duplicate requirement cards and provides unified legal status.
    """

    @classmethod
    def aggregate(
        cls,
        checks: List[Any],
        fields_map: Dict[str, Any],
        human_reviews: Optional[Dict[str, Any]] = None
    ) -> List[CanonicalRequirementGroup]:
        human_reviews = human_reviews or {}
        groups: List[CanonicalRequirementGroup] = []

        for defn in CANONICAL_REQUIREMENT_DEFINITIONS:
            cid = defn["canonical_id"]
            field_key = defn["field"]
            
            target_ids = set(defn.get("rule_ids", []))
            relevant_checks = [
                c for c in checks
                if c.rule_id in target_ids or getattr(c, "field", None) == field_key or (field_key == "manufacturing_date" and getattr(c, "field", None) == "packing_date")
            ]

            # Filter out checks marked NOT_APPLICABLE for status determination
            active_checks = [c for c in relevant_checks if c.status != "NOT_APPLICABLE"]

            sub_items: List[SubCheckItem] = []
            for c in relevant_checks:
                sub_items.append(SubCheckItem(
                    rule_id=c.rule_id,
                    rule_title=getattr(c, "requirement", c.rule_id),
                    section=getattr(c, "section", None) or getattr(c, "source_reference", None) or "Rule 6",
                    status=c.status,
                    reason=c.reason,
                    confidence=c.confidence,
                    extracted_value=c.extracted_value,
                    severity=getattr(c, "severity", "MEDIUM")
                ))

            # Fallback field alias lookup in fields_map
            extracted_val = None
            extracted_conf = 0.0
            for alias in [field_key, field_key.replace("_", ""), field_key.split("_")[0]]:
                if alias in fields_map:
                    f_obj = fields_map[alias]
                    raw_val = f_obj.get("raw_text") or f_obj.get("extracted_value") or f_obj.get("value")
                    if raw_val:
                        extracted_val = str(raw_val)
                        extracted_conf = float(f_obj.get("confidence", 0.90))
                        break

            # Determine aggregate status
            if not active_checks:
                if relevant_checks and any(c.status == "NOT_APPLICABLE" for c in relevant_checks):
                    status = "NOT_APPLICABLE"
                    overall_reason = f"Statutory check for {defn['title']} not applicable to this specific packaging category."
                    conf = 0.0
                else:
                    # If rule was required but no active check ran, it needs inspector review
                    status = "NEEDS_REVIEW"
                    overall_reason = f"Statutory requirement for {defn['title']} requires inspector physical package review."
                    conf = 0.0
            else:
                has_violation = any(c.status in ["NON_COMPLIANT", "POTENTIAL_VIOLATION", "CONFIRMED_VIOLATION"] for c in active_checks)
                has_review = any(c.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "MANUAL_CHECK_REQUIRED"] for c in active_checks)

                if has_violation:
                    status = "NON_COMPLIANT"
                    violating_checks = [c for c in active_checks if c.status in ["NON_COMPLIANT", "POTENTIAL_VIOLATION", "CONFIRMED_VIOLATION"]]
                    overall_reason = f"Potential non-compliance detected: {'; '.join(v.reason for v in violating_checks)}"
                elif has_review:
                    status = "NEEDS_REVIEW"
                    review_checks = [c for c in active_checks if c.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "MANUAL_CHECK_REQUIRED"]]
                    overall_reason = f"Manual inspector review required: {'; '.join(r.reason for r in review_checks)}"
                else:
                    status = "COMPLIANT"
                    overall_reason = f"All applicable statutory requirements for {defn['title']} verified and compliant."

                extracted_vals = [c.extracted_value for c in active_checks if c.extracted_value]
                if extracted_vals:
                    extracted_val = extracted_vals[0]
                    conf = sum(c.confidence for c in active_checks) / len(active_checks)
                elif extracted_val:
                    conf = extracted_conf
                else:
                    extracted_val = None
                    conf = 0.0

            # Check if an inspector manually reviewed this canonical requirement
            hr = human_reviews.get(cid)
            if hr:
                dec = hr.get("decision", status)
                if dec in ["INSUFFICIENT_EVIDENCE", "NEEDS_REVIEW"]:
                    status = "NEEDS_REVIEW"
                elif dec in ["NON_COMPLIANT", "CONFIRMED_VIOLATION"]:
                    status = "NON_COMPLIANT"
                elif dec in ["COMPLIANT", "CONFIRMED_COMPLIANT"]:
                    status = "COMPLIANT"
                else:
                    status = dec
                overall_reason = f"[Human-Verified by {hr.get('reviewer', 'Inspector')}]: {hr.get('reason', overall_reason)}"

            groups.append(CanonicalRequirementGroup(
                canonical_id=cid,
                title=defn["title"],
                statutory_rule=defn["statutory_rule"],
                field=field_key,
                status=status,
                extracted_value=extracted_val,
                confidence=round(conf, 2),
                overall_reason=overall_reason,
                sub_checks=sub_items,
                human_review=hr
            ))

        return groups
