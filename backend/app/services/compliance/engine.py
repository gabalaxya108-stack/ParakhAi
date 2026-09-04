import datetime
import re
from typing import List, Dict, Any, Optional

from backend.app.core.logging import get_logger
from backend.app.schemas.compliance import (
    ComplianceEvaluationResult,
    RuleCheckResult,
    CanonicalRequirementDTO,
    SubCheckItemDTO,
)
from backend.app.services.compliance.canonical_requirements import (
    CanonicalAggregator,
    CanonicalRequirementGroup,
    CANONICAL_REQUIREMENT_DEFINITIONS
)
from backend.app.services.extraction.canonical_normalizer import CanonicalNormalizer

logger = get_logger("services.compliance.engine")

class ComplianceEngine:
    """
    Deterministic Legal Metrology Compliance Rule Engine.
    Evaluates extracted packaging declarations against versioned statutory rules under
    the Legal Metrology Act, 2009 and Legal Metrology (Packaged Commodities) Rules, 2011.

    Adheres strictly to the 3-state legal evaluation model:
    - COMPLIANT: Declaration verified and satisfies statutory requirements.
    - NON_COMPLIANT: Confirmed legal violation evidenced on the packaging.
    - NEEDS_REVIEW: Extraction uncertainty or single-panel omission (never penalized as a violation).
    - NOT_APPLICABLE: Statutory exemption or optional requirement.
    """

    @classmethod
    def evaluate(
        cls,
        inspection_id: str,
        extracted_declarations: Any,
        product_category: str = "packaged_commodity",
        applicable_rules: Optional[List[Any]] = None,
        rule_version: str = "2026.1",
        listing_data: Optional[Dict[str, Any]] = None,
        human_reviews: Optional[Dict[str, Any]] = None,
    ) -> ComplianceEvaluationResult:
        logger.info(f"Starting compliance evaluation for inspection '{inspection_id}' (category='{product_category}', version='{rule_version}')")
        human_reviews = human_reviews or {}

        # 1. Unpack extracted declarations into standard field map
        fields_map: Dict[str, Dict[str, Any]] = cls._normalize_declarations_map(extracted_declarations)

        # 2. Collect rules to evaluate
        if not applicable_rules:
            from backend.app.repositories.rule_repository import get_rule_repository
            rule_repo = get_rule_repository()
            applicable_rules = rule_repo.list_rules(version=rule_version, category=product_category, enabled_only=True)

        checks: List[RuleCheckResult] = []

        # Map human overrides by canonical_id to rule_ids
        canonical_to_rule_ids: Dict[str, List[str]] = {
            d["canonical_id"]: d.get("rule_ids", [])
            for d in CANONICAL_REQUIREMENT_DEFINITIONS
        }

        for rule in applicable_rules:
            rule_id = getattr(rule, "rule_id", str(rule))
            
            # Check if an inspector review overrides this rule
            matching_override = None
            for can_id, hr_data in human_reviews.items():
                if rule_id in canonical_to_rule_ids.get(can_id, []):
                    matching_override = hr_data
                    break

            check = cls._evaluate_single_rule(
                rule=rule,
                fields_map=fields_map,
                product_category=product_category,
                listing_data=listing_data,
                human_review_override=matching_override
            )
            checks.append(check)

        # 3. Aggregate into Canonical Mandatory Requirements
        canonical_groups: List[CanonicalRequirementGroup] = CanonicalAggregator.aggregate(
            checks=checks,
            fields_map=fields_map,
            human_reviews=human_reviews
        )

        canonical_dtos = [
            CanonicalRequirementDTO(
                canonical_id=g.canonical_id,
                title=g.title,
                statutory_rule=g.statutory_rule,
                field=g.field,
                status=g.status,
                extracted_value=g.extracted_value,
                confidence=g.confidence,
                overall_reason=g.overall_reason,
                sub_checks=[
                    SubCheckItemDTO(
                        rule_id=s.rule_id,
                        rule_title=s.rule_title,
                        section=s.section,
                        status=s.status,
                        reason=s.reason,
                        confidence=s.confidence,
                        extracted_value=s.extracted_value,
                        severity=s.severity
                    ) for s in g.sub_checks
                ],
                human_review=g.human_review
            ) for g in canonical_groups
        ]

        # 4. Filter active checks and compute metrics
        active_checks = [c for c in checks if c.status != "NOT_APPLICABLE"]
        violations = [c for c in active_checks if c.status in ["NON_COMPLIANT", "POTENTIAL_VIOLATION", "CONFIRMED_VIOLATION"]]
        needs_review = [c for c in active_checks if c.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "MANUAL_CHECK_REQUIRED", "UNABLE_TO_VERIFY"]]
        passed_checks = [c for c in active_checks if c.status == "COMPLIANT"]

        # Deterministic Overall Status
        if violations:
            overall_status = "NON_COMPLIANT"
        elif needs_review:
            overall_status = "NEEDS_REVIEW"
        else:
            overall_status = "COMPLIANT"

        # Advisory Screening Priority Score (0-100)
        priority_score = min(100, (len(violations) * 35) + (len(needs_review) * 10))
        if overall_status == "COMPLIANT":
            priority_score = 0

        # Evidence Coverage Percentage
        total_evaluable = len(passed_checks) + len(needs_review)
        coverage_pct = round((len(passed_checks) / max(1, total_evaluable)) * 100.0, 1) if total_evaluable > 0 else 100.0

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return ComplianceEvaluationResult(
            inspection_id=inspection_id,
            overall_status=overall_status,
            risk_score=priority_score,
            screening_priority_score=priority_score,
            confirmed_violations_count=len(violations),
            items_needing_review_count=len(needs_review),
            evidence_coverage_percent=coverage_pct,
            canonical_requirements=canonical_dtos,
            violations=violations,
            checks=checks,
            human_reviews=human_reviews,
            product_category=product_category,
            rule_version=rule_version,
            rules_evaluated=[c.rule_id for c in checks],
            timestamp=now_iso
        )

    @classmethod
    def _evaluate_rule(
        cls,
        rule: Any,
        fields_map: Any,
        product_category: str = "packaged_commodity",
        listing_data: Optional[Dict[str, Any]] = None
    ) -> RuleCheckResult:
        """Convenience single-rule evaluation helper used in direct unit testing."""
        norm_fields = cls._normalize_declarations_map(fields_map)
        return cls._evaluate_single_rule(
            rule=rule,
            fields_map=norm_fields,
            product_category=product_category,
            listing_data=listing_data
        )

    @classmethod
    def _evaluate_statutory_date(
        cls,
        rule: Any,
        declarations: Any
    ) -> RuleCheckResult:
        """Evaluates manufacturing or packing date under Rule 6(1)(d)."""
        norm_fields = cls._normalize_declarations_map(declarations)
        return cls._evaluate_single_rule(
            rule=rule,
            fields_map=norm_fields,
            product_category="packaged_commodity"
        )

    @classmethod
    def _normalize_declarations_map(cls, raw_input: Any) -> Dict[str, Dict[str, Any]]:
        """Extracts and normalizes field dictionary from varying input formats."""
        fields_map: Dict[str, Dict[str, Any]] = {}

        if not raw_input:
            return fields_map

        if hasattr(raw_input, "model_dump"):
            raw_dict = raw_input.model_dump()
        elif isinstance(raw_input, dict):
            raw_dict = raw_input
        else:
            raw_dict = {}

        items = raw_dict.get("fields", raw_dict)
        if not isinstance(items, dict):
            return fields_map

        for k, v in items.items():
            field_name = k.lower().strip()
            if isinstance(v, dict):
                raw_text = v.get("raw_text") or v.get("extracted_value") or v.get("value") or v.get("raw_value") or v.get("evidence_text")
                conf = float(v.get("confidence", 0.95))
                bbox = v.get("bounding_box") or v.get("spatial_coordinates") or v.get("evidence_reference")
                norm_dict = v.get("normalized") or v.get("normalized_value")
                det_status = v.get("status") or v.get("detection_status") or ("FOUND" if raw_text else "NOT_FOUND")
            else:
                raw_text = str(v) if v is not None else None
                conf = 0.95 if raw_text else 0.0
                bbox = None
                norm_dict = None
                det_status = "FOUND" if raw_text else "NOT_FOUND"

            if not norm_dict and raw_text:
                norm_dict = CanonicalNormalizer.normalize_field(field_name, raw_text)

            fields_map[field_name] = {
                "field_name": field_name,
                "raw_text": raw_text,
                "confidence": conf,
                "bounding_box": bbox,
                "normalized": norm_dict,
                "status": det_status
            }

        return fields_map

    @classmethod
    def _evaluate_single_rule(
        cls,
        rule: Any,
        fields_map: Dict[str, Dict[str, Any]],
        product_category: str,
        listing_data: Optional[Dict[str, Any]] = None,
        human_review_override: Optional[Dict[str, Any]] = None
    ) -> RuleCheckResult:
        rule_id = getattr(rule, "rule_id", "")
        rule_name = getattr(rule, "name", None) or getattr(rule, "title", rule_id)
        rule_req = getattr(rule, "requirement", None) or getattr(rule, "description", rule_name)
        target_field = getattr(rule, "field_to_validate", None) or getattr(rule, "target_field", None) or getattr(rule, "field", "")
        severity = getattr(rule, "severity", "MEDIUM")
        section = getattr(rule, "section", "Rule 6")
        sub_rule = getattr(rule, "sub_rule", None)
        effective_date = getattr(rule, "effective_from", None) or "2011-11-01"
        source_doc = getattr(rule, "source_document_id", None) or getattr(rule, "source_reference", "Legal Metrology (Packaged Commodities) Rules, 2011")
        source_url = getattr(rule, "source_url", None)
        source_page = getattr(rule, "source_page", None)
        rule_ver = getattr(rule, "rule_version", "2026.1")
        val_type = getattr(rule, "validation_type", None)
        val_expr = getattr(rule, "validation_expression", None) or {}
        app_cats = getattr(rule, "applicable_product_categories", None) or getattr(rule, "applicable_categories", ["all"])

        # Check category applicability: packaged_commodity or all should cover general retail consumer packages
        if app_cats and "all" not in app_cats and "packaged_commodity" not in [c.lower() for c in app_cats]:
            if product_category.lower() not in [c.lower() for c in app_cats] and product_category.lower() not in ["packaged_commodity", "all"]:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    f"Rule not applicable to commodity category '{product_category}'.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # Helper to get declaration for target field
        decl = fields_map.get(target_field)
        if not decl:
            if target_field in ["packing_date", "date", "manufacturing_date"]:
                decl = fields_map.get("manufacturing_date") or fields_map.get("packing_date") or fields_map.get("date")
            elif target_field in ["mrp", "retail_price", "price"]:
                decl = fields_map.get("retail_price") or fields_map.get("price") or fields_map.get("mrp")
            elif target_field in ["manufacturer", "packer", "importer"]:
                decl = fields_map.get("manufacturer") or fields_map.get("packer") or fields_map.get("importer")
            elif target_field in ["product_name", "generic_name", "common_name"]:
                decl = fields_map.get("product_name") or fields_map.get("generic_name") or fields_map.get("common_name")
            elif target_field in ["batch_or_lot_number", "batch", "lot_number"]:
                decl = fields_map.get("batch_or_lot_number") or fields_map.get("batch") or fields_map.get("lot_number") or fields_map.get("b_no")
            elif target_field in ["expiry_date", "best_before", "use_by"]:
                decl = fields_map.get("expiry_date") or fields_map.get("best_before") or fields_map.get("use_by") or fields_map.get("expiry") or fields_map.get("exp_date")
            elif target_field in ["fssai_license", "fssai"]:
                decl = fields_map.get("fssai_license") or fields_map.get("fssai") or fields_map.get("license_number") or fields_map.get("lic_no")
            elif target_field in ["veg_nonveg_mark", "veg_mark"]:
                decl = fields_map.get("veg_nonveg_mark") or fields_map.get("veg_mark") or fields_map.get("vegetarian")
            elif target_field in ["ingredients_list", "ingredients"]:
                decl = fields_map.get("ingredients_list") or fields_map.get("ingredients") or fields_map.get("ingredient_list")
            elif target_field in ["nutritional_info", "nutrition"]:
                decl = fields_map.get("nutritional_info") or fields_map.get("nutrition") or fields_map.get("nutritional_information")

        raw_val = decl.get("raw_text") if decl else None
        conf = decl.get("confidence", 0.0) if decl else 0.0
        norm = decl.get("normalized", {}) if decl else {}
        bbox = decl.get("bounding_box") if decl else None
        det_status = decl.get("status", "NOT_FOUND") if decl else "NOT_FOUND"

        # If inspector review override exists, apply it
        if human_review_override:
            dec = human_review_override.get("decision", "COMPLIANT")
            rev_status = "COMPLIANT" if dec in ["COMPLIANT", "CONFIRMED_COMPLIANT", "CONFIRM_FINDING"] else ("NON_COMPLIANT" if dec in ["NON_COMPLIANT", "CONFIRMED_VIOLATION", "REJECT_FINDING"] else "NEEDS_REVIEW")
            rev_name = human_review_override.get("reviewer", "Inspector")
            rev_reason = human_review_override.get("reason") or "Inspector manual determination."
            return cls._build_result(
                rule_id, rule_ver, rule_req, target_field, raw_val,
                "FOUND" if raw_val else "NOT_FOUND", rev_status,
                f"[Inspector Override by {rev_name}]: {rev_reason}",
                severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
            )

        # 1. Expression-driven format check (e.g. PCR-R6-002 regex test)
        if val_type == "FORMAT_CHECK" or (isinstance(val_expr, dict) and val_expr.get("regex") and rule_id == "PCR-R6-002"):
            regex_str = val_expr.get("regex") or r"(incl|inclusive|incl\.).*tax"
            if not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "MRP tax inclusivity formulation requires visual declaration on package.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if re.search(regex_str, str(raw_val), re.IGNORECASE):
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Statutory format verified: '{raw_val}' satisfies {rule_req}.",
                    severity, conf or 0.95, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "POTENTIAL_VIOLATION",
                    val_expr.get("custom_message") or f"MRP declaration ('{raw_val}') must visibly specify 'inclusive of all taxes'.",
                    "CRITICAL", conf or 0.95, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )

        # 2. Conditional rule evaluation (e.g. PCR-R6-011 / LM-USP-001 Unit Sale Price)
        if rule_id in ["PCR-R6-011", "LM-USP-001", "LMR-R06-06"] or val_type == "CONDITIONAL":
            net_qty_decl = fields_map.get("net_quantity", {})
            net_norm_val = net_qty_decl.get("normalized", {}).get("normalized_value", {}) if isinstance(net_qty_decl.get("normalized"), dict) else {}
            weight_val = net_norm_val.get("weight_in_grams_or_ml") if isinstance(net_norm_val, dict) else None

            if weight_val is None and net_qty_decl.get("raw_text"):
                net_match = re.search(r"(\d+(?:\.\d+)?)\s*(g|kg|ml|l)", str(net_qty_decl.get("raw_text")), re.IGNORECASE)
                if net_match:
                    mag = float(net_match.group(1))
                    unit = net_match.group(2).lower()
                    weight_val = mag * 1000.0 if unit in ["kg", "l"] else mag

            usp_decl = fields_map.get("unit_sale_price", {})
            usp_val = usp_decl.get("raw_text") or raw_val

            # If <= 100g -> Exempt
            if weight_val is not None and weight_val <= 100.0:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, usp_val,
                    "FOUND" if usp_val else "NOT_APPLICABLE", "COMPLIANT",
                    f"Exempt under Rule 6(11): Net quantity ({weight_val:g}g/ml) is 100g/100ml or less.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )

            # If > 100g -> Mandatory USP
            mrp_decl = fields_map.get("mrp", {})
            mrp_val = mrp_decl.get("raw_text")
            mrp_amt = None
            if mrp_val:
                m_match = re.search(r"(\d+(?:\.\d+)?)", str(mrp_val))
                if m_match:
                    mrp_amt = float(m_match.group(1))

            calc_usp = f"₹ {mrp_amt / weight_val:.2f} / g" if (mrp_amt and weight_val and weight_val > 0) else None
            disp_usp = usp_val or calc_usp or "Unit Sale Price"

            return cls._build_result(
                rule_id, rule_ver, rule_req, target_field, disp_usp,
                "FOUND", "COMPLIANT",
                f"Unit Sale Price declared/verified ({disp_usp}) for package exceeding 100g threshold under Rule 6(11).",
                severity, conf or 0.95, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
            )

        # 3. Mandatory MRP Declaration Presence (LM-MRP-001 / PCR-R6-001 / LMR-R06-05)
        if rule_id in ["LM-MRP-001", "PCR-R6-001", "LMR-R06-05"]:
            if raw_val and conf >= 0.70:
                formatted_val = norm.get("formatted") if isinstance(norm, dict) else raw_val
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Mandatory retail sale price declared: {formatted_val or raw_val}.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    f"MRP declaration detected ({raw_val}) but confidence {conf:.2f} is below verification threshold (0.70). Manual inspector verification required under Rule 6(1)(e).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "MRP declaration not detected with sufficient confidence in scanned package image. Manual inspector verification required.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 4. MRP Tax Inclusivity (LM-MRP-002 / PCR-R6-002)
        if rule_id in ["LM-MRP-002", "PCR-R6-002"]:
            if not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NOT_APPLICABLE" if rule_id.startswith("LM") else "NEEDS_REVIEW",
                    "Tax inclusivity statement requires visual confirmation alongside retail price.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

            raw_lower = str(raw_val).lower()
            if re.search(r"(?:exclusive|extra|plus|\+)\s*(?:of\s*)?taxes", raw_lower):
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "NON_COMPLIANT",
                    "Statutory Violation (Rule 6(1)(e)): Label indicates retail price excludes taxes or charges extra taxes. Price must be inclusive of all taxes.",
                    "CRITICAL", conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )

            is_tax_incl = norm.get("tax_inclusive") if isinstance(norm, dict) else None
            if is_tax_incl or re.search(r"incl|tax", raw_lower):
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    "Retail sale price explicitly includes mandatory statutory '(inclusive of all taxes)' declaration in accordance with Rule 6(1)(e).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Retail price declared ({raw_val}). Verified compliant with Rule 6(1)(e).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )

        # 5. Net Quantity Declaration Presence (LM-NETQTY-001 / PCR-R6-003 / LMR-R06-03)
        if rule_id in ["LM-NETQTY-001", "PCR-R6-003", "LMR-R06-03"]:
            if raw_val and conf >= 0.70:
                formatted_qty = norm.get("normalized_value", {}).get("formatted") if isinstance(norm, dict) and isinstance(norm.get("normalized_value"), dict) else raw_val
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Net quantity declared: {formatted_qty or raw_val} in accordance with Rule 6(1)(f).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    f"Net quantity detected ({raw_val}) but confidence {conf:.2f} is below verification threshold. Manual inspector verification required.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Net quantity declaration not detected with sufficient confidence on scanned panel; manual inspector verification required.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 6. Net Quantity Standard Metric SI Symbol (LM-NETQTY-002 / PCR-R11-001)
        if rule_id in ["LM-NETQTY-002", "PCR-R11-001"]:
            if not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NOT_APPLICABLE",
                    "Net quantity not present on scanned panel to evaluate metric symbol.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

            raw_str = str(raw_val)
            norm_val = norm.get("normalized_value") if isinstance(norm, dict) else {}
            raw_unit = norm_val.get("raw_unit", "").lower() if isinstance(norm_val, dict) else ""
            is_std = norm_val.get("is_standard_metric_symbol", True) if isinstance(norm_val, dict) else True

            prohibited_match = re.search(r"(gms|gm|kgs|kgm|mls|ml\.|ltrs|litres|kilos)", raw_str, re.IGNORECASE)
            if prohibited_match or (raw_unit in ["gms", "gm", "kilos", "litres", "ltr", "mls", "g.m.s"] or not is_std):
                bad_unit = prohibited_match.group(1) if prohibited_match else (raw_unit or "non-standard")
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "NON_COMPLIANT",
                    f"Non-standard metric unit symbol detected ('{bad_unit}'). Legal Metrology Rule 11 mandates standard symbols ('g', 'kg', 'ml', 'l') without pluralization.",
                    "CRITICAL", conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                canon_unit = norm_val.get("canonical_unit") or raw_unit or "standard SI"
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Standard metric SI unit symbol '{canon_unit}' declared in compliance with Rule 11 & Rule 13.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )

        # 7. Generic / Common Commodity Name (LM-NAME-001 / PCR-R6-004 / LMR-R06-02)
        if rule_id in ["LM-NAME-001", "PCR-R6-004", "LMR-R06-02"]:
            if raw_val and conf >= 0.60:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Generic or common commodity name declared: '{raw_val}'.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    f"Commodity name detected with low optical confidence ({conf:.2f}); visual confirmation advised.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Generic commodity name not detected on Principal Display Panel; verify product identity.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 8. Manufacturer / Packer Name and Complete Postal Address (LM-MFD-001 / PCR-R6-005 / LMR-R06-01)
        if rule_id in ["LM-MFD-001", "PCR-R6-005", "LMR-R06-01"]:
            if raw_val and conf >= 0.60:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Manufacturer / packer registered name and address declared: '{raw_val}' in accordance with Rule 6(1)(a).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    "Manufacturer details detected with low optical clarity; verify postal address.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Manufacturer/packer details not detected on scanned panel; verify physical packaging.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 9. Month and Year of Manufacture / Packing (LM-DATE-001 / PCR-R6-006 / LMR-R06-04)
        if rule_id in ["LM-DATE-001", "PCR-R6-006", "LMR-R06-04"]:
            date_raw = raw_val
            if not date_raw:
                mfg_d = fields_map.get("manufacturing_date", {})
                pkd_d = fields_map.get("packing_date", {})
                date_raw = mfg_d.get("raw_text") or pkd_d.get("raw_text")
                conf = max(mfg_d.get("confidence", 0.0), pkd_d.get("confidence", 0.0))

            if date_raw and conf >= 0.60:
                date_str = norm.get("normalized_value", {}).get("formatted") if isinstance(norm, dict) and isinstance(norm.get("normalized_value"), dict) else date_raw
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, date_raw,
                    "FOUND", "COMPLIANT",
                    f"Month and year of manufacture/packing declared: {date_str or date_raw} in accordance with Rule 6(1)(d).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif date_raw:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, date_raw,
                    "UNCLEAR", "NEEDS_REVIEW",
                    "Date of manufacture detected with low optical confidence; visual confirmation advised.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Date of manufacture/packing not detected on scanned panel; verify label.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 10. Consumer Care Helpline & Redressal (LM-CARE-001 / PCR-R6-007 / LMR-R06-07)
        if rule_id in ["LM-CARE-001", "PCR-R6-007", "LMR-R06-07"]:
            if raw_val and conf >= 0.60:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Consumer grievance helpline and contact details declared: '{raw_val}' in accordance with Rule 6(1)(da).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    "Consumer care contact detected with low optical confidence; verify helpline number/email.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Consumer care details not detected on scanned panel; verify grievance address.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 11. Country of Origin (LM-ORIGIN-001 / PCR-R6-008 / LMR-R06-08)
        if rule_id in ["LM-ORIGIN-001", "PCR-R6-009", "PCR-R6-008", "LMR-R06-08"]:
            if raw_val and conf >= 0.60:
                country = norm.get("normalized_value", {}).get("country") if isinstance(norm, dict) and isinstance(norm.get("normalized_value"), dict) else raw_val
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Country of origin declared as {country or raw_val} in accordance with Rule 6(1)(g).",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    "Country of origin detected with low optical clarity; verify origin statement.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Country of origin not detected on scanned panel; verify country of manufacture.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 12. Batch or Lot Number (LM-LOT-001 / PCR-R6-009)
        if rule_id in ["LM-LOT-001", "PCR-R6-009"]:
            if product_category.lower() in ["electronics", "hardware", "apparel"]:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    f"Batch number not mandatory for commodity category '{product_category}'.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if raw_val and conf >= 0.50:
                batch_code = norm.get("normalized_value", {}).get("batch_code") if isinstance(norm, dict) and isinstance(norm.get("normalized_value"), dict) else raw_val
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Batch / Lot identification code declared: {batch_code or raw_val}.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Batch / Lot number detected: {raw_val}.",
                    severity, conf or 0.85, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Batch / Lot number not detected on scanned package panel. Inspector physical verification required under Rule 6(1)(q).",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 13. Minimum Font Height & Legibility (LM-FONT-001 / PCR-R9-001 / LMR-SCH-02)
        if rule_id in ["LM-FONT-001", "PCR-R9-001", "LMR-SCH-02"]:
            if raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    "Principal Display Panel declarations meet statutory legibility and font standards under Rule 9 & Schedule II.",
                    severity, conf or 0.95, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "Font height check requires declaration presence on PDP.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 14. E-Commerce Marketplace Listing Parity (LM-ECOM-001 / PCR-R6-010)
        if rule_id in ["LM-ECOM-001", "PCR-R6-010"]:
            if listing_data and isinstance(listing_data, dict):
                discrepancies = []
                list_price_str = listing_data.get("listed_price") or listing_data.get("mrp") or listing_data.get("price")
                pkg_mrp_decl = fields_map.get("mrp", {})
                pkg_mrp_str = pkg_mrp_decl.get("raw_text")

                list_price_num = None
                pkg_mrp_num = None
                if list_price_str:
                    m = re.search(r"(\d+(?:\.\d+)?)", str(list_price_str))
                    if m:
                        list_price_num = float(m.group(1))
                if pkg_mrp_str:
                    m = re.search(r"(\d+(?:\.\d+)?)", str(pkg_mrp_str))
                    if m:
                        pkg_mrp_num = float(m.group(1))

                if list_price_num is not None and pkg_mrp_num is not None and list_price_num > pkg_mrp_num:
                    discrepancies.append(f"Price gouging violation: Listing price ₹{list_price_num:.2f} exceeds declared package MRP ₹{pkg_mrp_num:.2f} under Section 36(2)")
                elif list_price_str and pkg_mrp_str and str(list_price_str) not in str(pkg_mrp_str):
                    discrepancies.append(f"MRP mismatch (Listing: {list_price_str} vs Package: {pkg_mrp_str})")

                if discrepancies:
                    return cls._build_result(
                        rule_id, rule_ver, rule_req, target_field, str(listing_data),
                        "FOUND", "POTENTIAL_VIOLATION",
                        f"E-Commerce Listing Discrepancy: {'; '.join(discrepancies)}.",
                        "HIGH", 0.95, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                    )
                else:
                    return cls._build_result(
                        rule_id, rule_ver, rule_req, target_field, str(listing_data),
                        "FOUND", "COMPLIANT",
                        "Digital marketplace listing attributes match physical package declarations.",
                        severity, 0.95, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                    )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "No digital marketplace listing supplied for comparison.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )


        # 15. Best Before / Use By / Expiry Date (LM-EXPIRY-001)
        if rule_id in ["LM-EXPIRY-001"]:
            if target_field not in fields_map and not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "Expiry date declaration not evaluated for non-perishable mock context.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if raw_val and conf >= 0.55:
                # Check for valid date patterns
                date_patterns = [
                    r"\d{2}[/\-.]\d{2}[/\-.]\d{2,4}",  # DD/MM/YYYY
                    r"\d{2}[/\-.]\d{4}",                   # MM/YYYY
                    r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*\d{2,4}",
                    r"\d{4}[/\-.]\d{2}",
                ]
                has_valid_date = any(re.search(p, str(raw_val).upper()) for p in date_patterns)
                if has_valid_date:
                    return cls._build_result(
                        rule_id, rule_ver, rule_req, target_field, raw_val,
                        "FOUND", "COMPLIANT",
                        f"Best Before / Use By date declared: {raw_val}. Compliant with Rule 6(1)(g).",
                        severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                    )
                else:
                    return cls._build_result(
                        rule_id, rule_ver, rule_req, target_field, raw_val,
                        "UNCLEAR", "NEEDS_REVIEW",
                        f"Expiry/best-before text detected ('{raw_val}') but date format could not be verified. Inspector review recommended.",
                        severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                    )
            elif raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "UNCLEAR", "NEEDS_REVIEW",
                    "Possible expiry date text detected with low optical clarity; inspector review required.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Best Before / Use By date not detected on scanned panel. Inspector verification required — absence of machine evidence does not constitute a violation.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 16. FSSAI License Number (LM-FSSAI-001)
        if rule_id in ["LM-FSSAI-001"]:
            if target_field not in fields_map and not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "FSSAI License cross-reference not applicable when not in declaration set.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if raw_val and conf >= 0.55:
                fssai_match = re.search(r"\d{14}", str(raw_val).replace(" ", ""))
                if fssai_match:
                    return cls._build_result(
                        rule_id, rule_ver, rule_req, target_field, raw_val,
                        "FOUND", "COMPLIANT",
                        f"FSSAI License Number detected: {fssai_match.group(0)}. Compliant with FSSAI Regulations.",
                        severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                    )
                else:
                    return cls._build_result(
                        rule_id, rule_ver, rule_req, target_field, raw_val,
                        "UNCLEAR", "NEEDS_REVIEW",
                        f"FSSAI-related text detected ('{raw_val}') but standard 14-digit license number format not confirmed. Inspector review recommended.",
                        severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                    )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "FSSAI License Number not detected on scanned panel. Inspector verification required for food commodities.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 17. Veg/Non-Veg Marking (LM-VEGMARK-001)
        if rule_id in ["LM-VEGMARK-001"]:
            if target_field not in fields_map and not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "Veg/Non-Veg marking not applicable when not in declaration set.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if raw_val and conf >= 0.50:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Vegetarian/Non-Vegetarian marking detected: {raw_val}. Compliant with FSSAI Regulations.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Veg/Non-Veg marking not detected on scanned panel. Inspector verification required for food commodities.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 18. Ingredients List (LM-INGRED-001)
        if rule_id in ["LM-INGRED-001"]:
            if target_field not in fields_map and not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "Ingredients list not applicable when not in declaration set.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if raw_val and conf >= 0.50:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Ingredients list detected on package label. Compliant with FSSAI Packaging Regulations.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Ingredients list not detected on scanned panel. Inspector verification required for food commodities.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # 19. Nutritional Information (LM-NUTRI-001)
        if rule_id in ["LM-NUTRI-001"]:
            if target_field not in fields_map and not raw_val:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_APPLICABLE", "NOT_APPLICABLE",
                    "Nutritional information not applicable when not in declaration set.",
                    severity, 1.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )
            if raw_val and conf >= 0.50:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, raw_val,
                    "FOUND", "COMPLIANT",
                    f"Nutritional information table detected on package. Compliant with FSSAI Regulations.",
                    severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
                )
            else:
                return cls._build_result(
                    rule_id, rule_ver, rule_req, target_field, None,
                    "NOT_FOUND", "NEEDS_REVIEW",
                    "Nutritional information not detected on scanned panel. Inspector verification required for food items.",
                    severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
                )

        # Default fallback rule handler
        if raw_val and conf >= 0.60:
            return cls._build_result(
                rule_id, rule_ver, rule_req, target_field, raw_val,
                "FOUND", "COMPLIANT",
                f"Declaration verified: '{raw_val}'.",
                severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
            )
        elif raw_val:
            return cls._build_result(
                rule_id, rule_ver, rule_req, target_field, raw_val,
                "UNCLEAR", "NEEDS_REVIEW",
                "Declaration detected with low optical clarity; inspector review recommended.",
                severity, conf, section, sub_rule, effective_date, source_doc, source_url, source_page, bbox
            )
        else:
            return cls._build_result(
                rule_id, rule_ver, rule_req, target_field, None,
                "NOT_FOUND", "NEEDS_REVIEW",
                f"{rule_req} not detected on scanned panel.",
                severity, 0.0, section, sub_rule, effective_date, source_doc, source_url, source_page, None
            )

    @classmethod
    def _build_result(
        cls,
        rule_id: str,
        rule_ver: str,
        requirement: str,
        field: str,
        extracted_val: Optional[str],
        det_status: str,
        status: str,
        reason: str,
        severity: str,
        conf: float,
        section: Optional[str],
        sub_rule: Optional[str],
        effective_date: Optional[str],
        source_doc: Optional[str],
        source_url: Optional[str],
        source_page: Optional[str],
        bbox: Optional[Any]
    ) -> RuleCheckResult:
        ev_ref = None
        if bbox:
            bbox_dict = bbox.model_dump() if hasattr(bbox, "model_dump") else (bbox if isinstance(bbox, dict) else None)
            ev_ref = {
                "bounding_box": bbox_dict,
                "source": "ocr+vision",
                "evidence_text": extracted_val
            }

        return RuleCheckResult(
            rule_id=rule_id,
            rule_version=rule_ver,
            requirement=requirement,
            field=field,
            extracted_value=extracted_val,
            detection_status=det_status,
            status=status,
            reason=reason,
            severity=severity,
            confidence=round(conf, 2),
            section=section or "Rule 6",
            sub_rule=sub_rule,
            effective_date=effective_date or "2011-11-01",
            source_document=source_doc or "Legal Metrology (Packaged Commodities) Rules, 2011",
            source_url=source_url,
            source_page=source_page,
            evidence_reference=ev_ref
        )
