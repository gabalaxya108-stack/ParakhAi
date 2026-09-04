import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from backend.app.schemas.extraction import ExtractedDeclarationDTO, DeclarationType
from backend.app.schemas.rules import (
    RuleEvaluationResult,
    ComplianceStatus,
    ComplianceScorecard,
    RuleSeverity
)
from backend.app.services.rule_engine.catalog import CODIFIED_RULES

class LegalMetrologyRuleEngine:
    """
    Deterministic Legal Metrology Compliance Rule Engine.
    Executes versioned, codified legal rules against structured package declarations.
    Decoupled from LLM/AI layers.
    """

    @classmethod
    def evaluate(
        cls,
        declarations: List[ExtractedDeclarationDTO],
        pdp_area_sq_cm: float = 240.0,
        commodity_category: str = "Food & Beverages",
        overrides: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> ComplianceScorecard:
        """
        Runs all codified rules against the extracted declarations.
        Returns a complete ComplianceScorecard.
        """
        # Map declarations by type for O(1) lookup
        decl_map: Dict[DeclarationType, List[ExtractedDeclarationDTO]] = {}
        for d in declarations:
            decl_map.setdefault(d.declaration_type, []).append(d)

        results: List[RuleEvaluationResult] = []

        # 1. Rule 6(1)(a): Name and Address of Manufacturer / Packer
        results.append(cls._evaluate_manufacturer_address(decl_map.get(DeclarationType.NAME_AND_ADDRESS, [])))

        # 2. Rule 6(1)(b): Generic Commodity Name
        results.append(cls._evaluate_generic_name(decl_map.get(DeclarationType.GENERIC_NAME, [])))

        # 3. Rule 6(1)(c): Net Quantity & Legal SI Units
        net_qty_decls = decl_map.get(DeclarationType.NET_QUANTITY, [])
        results.append(cls._evaluate_net_quantity_units(net_qty_decls))

        # 4. Rule 6(1)(d): Month and Year of Manufacture / Packing
        results.append(cls._evaluate_manufacture_date(decl_map.get(DeclarationType.DATE_OF_MANUFACTURE, [])))

        # 5. Rule 6(1)(e): MRP Format and All Taxes Inclusivity
        mrp_decls = decl_map.get(DeclarationType.RETAIL_SALE_PRICE, [])
        results.append(cls._evaluate_mrp(mrp_decls))

        # 6. Rule 6(11): Unit Sale Price (USP)
        results.append(cls._evaluate_unit_sale_price(
            usp_decls=decl_map.get(DeclarationType.UNIT_SALE_PRICE, []),
            net_qty_decls=net_qty_decls,
            mrp_decls=mrp_decls
        ))

        # 7. Rule 6(1)(n): Consumer Care Helpline
        results.append(cls._evaluate_consumer_care(decl_map.get(DeclarationType.CONSUMER_CARE, [])))

        # 8. Rule 6(10): Country of Origin
        results.append(cls._evaluate_country_of_origin(
            decl_map.get(DeclarationType.COUNTRY_OF_ORIGIN, []),
            commodity_category=commodity_category
        ))

        # 9. Schedule II: Minimum Height of Numerals & Letters vs PDP Area
        results.append(cls._evaluate_schedule_ii_font_height(
            net_qty_decls=net_qty_decls,
            pdp_area_sq_cm=pdp_area_sq_cm
        ))

        # Apply inspector overrides if provided
        if overrides:
            for r in results:
                if r.rule_id in overrides:
                    ov = overrides[r.rule_id]
                    r.inspector_override = True
                    r.override_verdict = ov.get("override_verdict")
                    r.override_reason = ov.get("override_reason")
                    r.overridden_by = ov.get("overridden_by", "Inspector")

        # Calculate scorecard summary
        passed = 0
        failed = 0
        warning = 0
        manual = 0

        for r in results:
            effective_status = r.override_verdict if r.inspector_override and r.override_verdict else r.status
            if effective_status == ComplianceStatus.PASS:
                passed += 1
            elif effective_status == ComplianceStatus.FAIL:
                failed += 1
            elif effective_status == ComplianceStatus.WARNING:
                warning += 1
            else:
                manual += 1

        if failed > 0:
            overall = ComplianceStatus.FAIL
        elif manual > 0:
            overall = ComplianceStatus.MANUAL_CHECK_REQUIRED
        elif warning > 0:
            overall = ComplianceStatus.WARNING
        else:
            overall = ComplianceStatus.PASS

        return ComplianceScorecard(
            overall_status=overall,
            total_rules=len(results),
            passed_count=passed,
            failed_count=failed,
            warning_count=warning,
            manual_check_count=manual,
            results=results
        )

    # ------------------ RULE EVALUATORS ------------------

    @classmethod
    def _evaluate_manufacturer_address(cls, decls: List[ExtractedDeclarationDTO]) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-01")
        if not decls:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Mandatory declaration of Manufacturer / Packer name and address is missing from the package.",
                legal_citation="Rule 6(1)(a) mandates prominent display of manufacturer and packer identity and complete address.",
                recommended_action="Issue formal inquiry notice under Section 36(1) of Legal Metrology Act, 2009."
            )

        decl = decls[0]
        text = decl.raw_text.lower()
        has_keywords = any(kw in text for kw in ["mfd", "manufactured", "packed", "pkd", "imported", "marketed", "mfg"])
        # Check for 6 digit Indian PIN code
        has_pincode = bool(re.search(r'\b[1-9][0-9]{5}\b', decl.raw_text))

        if not has_keywords:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.WARNING,
                violation_reason="Manufacturer entity role not explicitly qualified (missing 'Manufactured by' or 'Packed by').",
                legal_citation="Rule 6(1)(a) requires explicit qualification of manufacturer vs packer status.",
                recommended_action="Verify manufacturer vs third-party packer contract documentation.",
                evidence_text=decl.raw_text,
                evidence_boxes=[decl.bounding_box]
            )

        if not has_pincode:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=RuleSeverity.MINOR,
                status=ComplianceStatus.WARNING,
                violation_reason="Complete postal address appears to omit postal PIN code.",
                legal_citation="Rule 6(1)(a) mandates complete physical address to enable consumer contact.",
                recommended_action="Require manufacturer to include 6-digit postal code on subsequent production batches.",
                evidence_text=decl.raw_text,
                evidence_boxes=[decl.bounding_box]
            )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(1)(a). Complete manufacturer identity and address declared.",
            evidence_text=decl.raw_text,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_generic_name(cls, decls: List[ExtractedDeclarationDTO]) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-02")
        if not decls or not decls[0].raw_text.strip():
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Generic or common name of the commodity is missing from the Principal Display Panel.",
                legal_citation="Rule 6(1)(b) mandates common or generic name to be displayed prominently on the PDP.",
                recommended_action="Issue violation notice requiring generic commodity identification."
            )

        decl = decls[0]
        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(1)(b). Generic commodity name displayed on PDP.",
            evidence_text=decl.raw_text,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_net_quantity_units(cls, decls: List[ExtractedDeclarationDTO]) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-03")
        if not decls:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Net quantity declaration is entirely missing.",
                legal_citation="Rule 6(1)(c) mandates net quantity declaration in terms of standard unit.",
                recommended_action="Severe violation: Package cannot be offered for retail sale without net quantity."
            )

        decl = decls[0]
        raw = decl.raw_text
        lower = raw.lower()

        # Check for strictly illegal abbreviations under Rule 13 / Fifth Schedule
        prohibited_tokens = [
            (r'\bgms\b', "gms", "Use standard symbol 'g'"),
            (r'\bgm\b', "gm", "Use standard symbol 'g'"),
            (r'\bg\.\b', "g.", "Trailing period after symbol is prohibited"),
            (r'\bkilos\b', "kilos", "Use standard symbol 'kg'"),
            (r'\bkgs\b', "kgs", "Use standard symbol 'kg'"),
            (r'\bkg\.\b', "kg.", "Trailing period after symbol is prohibited"),
            (r'\blitres\b', "litres", "Use standard symbol 'l' or 'L'"),
            (r'\blitre\b', "litre", "Use standard symbol 'l' or 'L'"),
            (r'\bltr\b', "ltr", "Use standard symbol 'l' or 'L'"),
            (r'\bltrs\b', "ltrs", "Use standard symbol 'l' or 'L'"),
            (r'\bml\.\b', "ml.", "Trailing period after symbol is prohibited"),
        ]

        for pattern, token, suggestion in prohibited_tokens:
            if re.search(pattern, lower):
                return RuleEvaluationResult(
                    rule_id=rule_def.rule_id,
                    legal_reference=rule_def.legal_reference,
                    rule_title=rule_def.title,
                    severity=rule_def.severity,
                    status=ComplianceStatus.FAIL,
                    violation_reason=f"Illegal non-standard unit symbol '{token}' used. {suggestion}.",
                    legal_citation="Rule 13 & Fifth Schedule explicitly prohibit pluralized or non-SI symbols such as 'gms' or 'ltr'. Only standard SI units ('g', 'kg', 'ml', 'l') are permitted without trailing periods.",
                    recommended_action="Direct manufacturer to stop circulation of non-compliant batch and correct die/plates.",
                    evidence_text=raw,
                    evidence_boxes=[decl.bounding_box]
                )

        # Validate standard SI symbol presence
        valid_unit_pattern = r'\b(\d+(?:\.\d+)?)\s*(kg|g|ml|l|L|m|cm|mm|N|U)\b'
        match = re.search(valid_unit_pattern, raw)
        if not match:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.MANUAL_CHECK_REQUIRED,
                violation_reason="Net quantity format does not match standard SI numerical notation.",
                legal_citation="Rule 6(1)(c) mandates clear numeral followed by authorized unit symbol.",
                recommended_action="Inspector manual verification required.",
                evidence_text=raw,
                evidence_boxes=[decl.bounding_box]
            )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(1)(c) and Rule 13. Net quantity correctly uses authorized standard SI unit.",
            evidence_text=raw,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_manufacture_date(cls, decls: List[ExtractedDeclarationDTO]) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-04")
        if not decls:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Month and Year of manufacture / packing / import is not declared.",
                legal_citation="Rule 6(1)(d) mandates month and year of manufacture or pre-packing.",
                recommended_action="Issue violation notice for missing manufacturing/packing date."
            )

        decl = decls[0]
        raw = decl.raw_text

        # Anti-post-dating validation: check for future years (> 2026)
        future_match = re.search(r'\b20(2[7-9]|[3-9][0-9])\b', raw)
        if future_match:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason=f"Illegal future manufacturing/import date '{future_match.group(0)}' declared (Post-dating violation).",
                legal_citation="Rule 6(1)(d) prohibits post-dating of packaging commodities.",
                recommended_action="Seize post-dated commodities and initiate penalty proceedings under Section 36(1).",
                evidence_text=raw,
                evidence_boxes=[decl.bounding_box]
            )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(1)(d). Month and year clearly declared.",
            evidence_text=raw,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_mrp(cls, decls: List[ExtractedDeclarationDTO]) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-05")
        if not decls:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Maximum Retail Price (MRP) declaration is completely missing.",
                legal_citation="Rule 6(1)(e) requires retail sale price to be declared on every package.",
                recommended_action="Prohibit sale of package without declared Maximum Retail Price."
            )

        decl = decls[0]
        raw = decl.raw_text
        lower = raw.lower()

        # Check for currency indicator
        has_currency = any(curr in raw for curr in ["₹", "Rs.", "Rs", "INR", "/-"])
        
        # Check mandatory "inclusive of all taxes"
        has_taxes = any(t in lower for t in [
            "incl. of all taxes",
            "inclusive of all taxes",
            "incl of all taxes",
            "incl. of taxes",
            "all taxes included"
        ])

        if not has_taxes:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="MRP declaration lacks mandatory phrase '(inclusive of all taxes)'.",
                legal_citation="Rule 6(1)(e) strictly mandates the statement 'inclusive of all taxes' or 'incl. of all taxes' with MRP.",
                recommended_action="Issue statutory notice for misleading price declaration under Rule 6(1)(e).",
                evidence_text=raw,
                evidence_boxes=[decl.bounding_box]
            )

        if not has_currency:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=RuleSeverity.MAJOR,
                status=ComplianceStatus.WARNING,
                violation_reason="MRP numeral is not preceded by standard Rupee symbol (₹) or 'Rs.'.",
                legal_citation="Rule 6(1)(e) requires price to be declared in Indian currency notation.",
                recommended_action="Advise packer to include ₹ symbol on retail display.",
                evidence_text=raw,
                evidence_boxes=[decl.bounding_box]
            )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(1)(e). MRP contains currency symbol and mandatory tax inclusivity clause.",
            evidence_text=raw,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_unit_sale_price(
        cls,
        usp_decls: List[ExtractedDeclarationDTO],
        net_qty_decls: List[ExtractedDeclarationDTO],
        mrp_decls: List[ExtractedDeclarationDTO]
    ) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-06")

        # Determine net quantity magnitude
        qty_val = 0.0
        unit = "g"
        if net_qty_decls:
            qty_decl = net_qty_decls[0]
            attrs = qty_decl.parsed_attributes
            qty_val = float(attrs.get("amount", 0.0)) if attrs.get("amount") else 0.0
            unit = attrs.get("unit", "g").lower()
            if not qty_val:
                m = re.search(r'(\d+(?:\.\d+)?)', qty_decl.raw_text)
                if m:
                    qty_val = float(m.group(1))

        # Check if USP is legally mandatory (> 100g or > 100ml or > 1 piece)
        is_mandatory = False
        if unit in ["g", "gm", "gms", "ml"] and qty_val > 100.0:
            is_mandatory = True
        elif unit in ["kg", "l", "litre", "litres"] and qty_val >= 0.1:
            is_mandatory = True

        if not usp_decls:
            if is_mandatory:
                return RuleEvaluationResult(
                    rule_id=rule_def.rule_id,
                    legal_reference=rule_def.legal_reference,
                    rule_title=rule_def.title,
                    severity=rule_def.severity,
                    status=ComplianceStatus.FAIL,
                    violation_reason=f"Unit Sale Price (USP) is missing for package of net quantity {qty_val}{unit} (> 100g/ml threshold).",
                    legal_citation="Rule 6(11) (2022 Amendment) mandates Unit Sale Price for all packaged commodities exceeding 100g or 100ml.",
                    recommended_action="Issue violation notice under Rule 6(11) for failure to declare Unit Sale Price."
                )
            else:
                return RuleEvaluationResult(
                    rule_id=rule_def.rule_id,
                    legal_reference=rule_def.legal_reference,
                    rule_title=rule_def.title,
                    severity=RuleSeverity.MINOR,
                    status=ComplianceStatus.PASS,
                    legal_citation="Exempt from Rule 6(11): Net quantity does not exceed 100g / 100ml threshold."
                )

        # USP is declared: check mathematical accuracy against MRP
        usp_decl = usp_decls[0]
        raw_usp = usp_decl.raw_text
        declared_amount = usp_decl.parsed_attributes.get("amount")

        mrp_amount = None
        if mrp_decls:
            mrp_amount = mrp_decls[0].parsed_attributes.get("amount")
            if not mrp_amount:
                m = re.search(r'(\d+(?:\.\d+)?)', mrp_decls[0].raw_text)
                if m:
                    mrp_amount = float(m.group(1))

        if mrp_amount and qty_val > 0 and declared_amount:
            # Normalized expected USP per gram/ml
            expected_per_unit = mrp_amount / qty_val
            declared_val = float(declared_amount)

            # Account for per-100g/ml declarations
            if "100" in raw_usp:
                expected_per_unit *= 100.0

            ratio = declared_val / expected_per_unit if expected_per_unit > 0 else 1.0
            if ratio < 0.90 or ratio > 1.10:
                return RuleEvaluationResult(
                    rule_id=rule_def.rule_id,
                    legal_reference=rule_def.legal_reference,
                    rule_title=rule_def.title,
                    severity=RuleSeverity.CRITICAL,
                    status=ComplianceStatus.FAIL,
                    violation_reason=f"Misleading Unit Sale Price: Declared {raw_usp} differs from calculated MRP/NetQty (₹{round(expected_per_unit, 2)}).",
                    legal_citation="Rule 6(11) mandates that declared Unit Sale Price must accurately reflect the Maximum Retail Price divided by quantity.",
                    recommended_action="Initiate false declaration penalty proceedings under Legal Metrology Act.",
                    evidence_text=raw_usp,
                    evidence_boxes=[usp_decl.bounding_box]
                )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(11). Unit Sale Price declared and mathematically verified.",
            evidence_text=raw_usp,
            evidence_boxes=[usp_decl.bounding_box]
        )

    @classmethod
    def _evaluate_consumer_care(cls, decls: List[ExtractedDeclarationDTO]) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-07")
        if not decls:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Consumer care / grievance contact details are missing entirely.",
                legal_citation="Rule 6(1)(n) mandates name, address, telephone number, and email address for consumer grievances.",
                recommended_action="Issue compliance notice requiring consumer grievance redressal contact info."
            )

        decl = decls[0]
        raw = decl.raw_text
        has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw))
        has_phone = bool(re.search(r'(?:\+91[\-\s]?)?[6-9]\d{9}|1800[\-\s]?\d{3,4}[\-\s]?\d{3,4}', raw))

        if not has_email and not has_phone:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=RuleSeverity.MAJOR,
                status=ComplianceStatus.FAIL,
                violation_reason="Consumer care info lacks both email address and helpline telephone number.",
                legal_citation="Rule 6(1)(n) requires telephone number and email address for direct consumer grievance access.",
                recommended_action="Mandate addition of helpline number and email address.",
                evidence_text=raw,
                evidence_boxes=[decl.bounding_box]
            )

        if not has_email:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=RuleSeverity.MINOR,
                status=ComplianceStatus.WARNING,
                violation_reason="Telephone helpline provided, but electronic email contact is omitted.",
                legal_citation="Rule 6(1)(n) specifies email address as a mandatory consumer channel.",
                recommended_action="Notify manufacturer to include official consumer email on packaging.",
                evidence_text=raw,
                evidence_boxes=[decl.bounding_box]
            )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(1)(n). Full consumer helpline and email grievance contact provided.",
            evidence_text=raw,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_country_of_origin(
        cls,
        decls: List[ExtractedDeclarationDTO],
        commodity_category: str
    ) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-R06-08")
        if not decls:
            # Especially critical for electronics/imported goods
            severity = RuleSeverity.CRITICAL if "Electronic" in commodity_category or "Import" in commodity_category else RuleSeverity.MAJOR
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=severity,
                status=ComplianceStatus.FAIL,
                violation_reason="Country of Origin / Country of Manufacture declaration is missing.",
                legal_citation="Rule 6(10) mandates clear declaration of the country of origin or manufacture on all packaged goods.",
                recommended_action="Issue violation notice under Rule 6(10) for imported / packaged commodity."
            )

        decl = decls[0]
        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation="Complies with Rule 6(10). Country of origin clearly stated.",
            evidence_text=decl.raw_text,
            evidence_boxes=[decl.bounding_box]
        )

    @classmethod
    def _evaluate_schedule_ii_font_height(
        cls,
        net_qty_decls: List[ExtractedDeclarationDTO],
        pdp_area_sq_cm: float
    ) -> RuleEvaluationResult:
        rule_def = next(r for r in CODIFIED_RULES if r.rule_id == "LMR-SCH-02")

        # Schedule II Table: Min numeral height vs PDP Area
        # Area <= 50: min 1.5mm (numeral), 1.0mm (letter)
        # 50 < Area <= 100: min 2.0mm (numeral), 1.5mm (letter)
        # 100 < Area <= 500: min 4.0mm (numeral), 2.5mm (letter)
        # Area > 500: min 6.0mm (numeral), 4.0mm (letter)
        if pdp_area_sq_cm <= 50.0:
            req_numeral_mm = 1.5
            req_letter_mm = 1.0
        elif pdp_area_sq_cm <= 100.0:
            req_numeral_mm = 2.0
            req_letter_mm = 1.5
        elif pdp_area_sq_cm <= 500.0:
            req_numeral_mm = 4.0
            req_letter_mm = 2.5
        else:
            req_numeral_mm = 6.0
            req_letter_mm = 4.0

        if not net_qty_decls:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason=f"Cannot verify font height because net quantity declaration is missing on PDP ({pdp_area_sq_cm} sq cm).",
                legal_citation="Schedule II specifies mandatory minimum height of numerals based on Principal Display Panel area."
            )

        decl = net_qty_decls[0]
        measured_h_mm = decl.bounding_box.estimated_font_height_mm

        # If font height was not measurable via DPI scale, mark for manual check
        if measured_h_mm is None or measured_h_mm <= 0.0:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=RuleSeverity.MINOR,
                status=ComplianceStatus.MANUAL_CHECK_REQUIRED,
                violation_reason=f"Requires optical gauge verification. For PDP area of {pdp_area_sq_cm} sq cm, Schedule II requires minimum numeral height of {req_numeral_mm}mm.",
                legal_citation="Schedule II prescribes minimum numeral and letter heights.",
                recommended_action="Inspector should verify physical font size with standard metrology magnifier gauge.",
                evidence_text=decl.raw_text,
                evidence_boxes=[decl.bounding_box]
            )

        if measured_h_mm < req_numeral_mm:
            return RuleEvaluationResult(
                rule_id=rule_def.rule_id,
                legal_reference=rule_def.legal_reference,
                rule_title=rule_def.title,
                severity=rule_def.severity,
                status=ComplianceStatus.FAIL,
                violation_reason=f"Numeral font height measured at {measured_h_mm}mm on PDP of {pdp_area_sq_cm} sq cm. Schedule II requires minimum {req_numeral_mm}mm.",
                legal_citation=f"Schedule II Table prescribes minimum numeral height of {req_numeral_mm}mm for packaging with PDP area {pdp_area_sq_cm} sq cm.",
                recommended_action="Issue notice to enlarge net quantity and numeral font size on packaging plate.",
                evidence_text=f"{decl.raw_text} (Height: {measured_h_mm}mm vs required {req_numeral_mm}mm)",
                evidence_boxes=[decl.bounding_box]
            )

        return RuleEvaluationResult(
            rule_id=rule_def.rule_id,
            legal_reference=rule_def.legal_reference,
            rule_title=rule_def.title,
            severity=rule_def.severity,
            status=ComplianceStatus.PASS,
            legal_citation=f"Complies with Schedule II. Measured numeral height ({measured_h_mm}mm) meets or exceeds requirement ({req_numeral_mm}mm for {pdp_area_sq_cm} sq cm PDP).",
            evidence_text=f"{decl.raw_text} ({measured_h_mm}mm)",
            evidence_boxes=[decl.bounding_box]
        )
