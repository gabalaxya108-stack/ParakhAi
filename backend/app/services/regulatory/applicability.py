from typing import List, Dict, Any, Optional
from backend.app.schemas.regulatory import RegulatoryRuleDTO

class ApplicabilityEngine:
    """
    Determines statutory applicability of Legal Metrology and Cross-Regulatory
    rules based on commodity characteristics, package type, and regulatory domain.
    """

    FOOD_CATEGORIES = {
        "food_packaged_commodity", "food", "edible", "beverage",
        "confectionery", "dairy", "spices", "snacks"
    }

    WHOLESALE_OR_INSTITUTIONAL = {
        "wholesale", "industrial", "institutional_consumer"
    }

    @classmethod
    def evaluate_applicability(
        cls,
        rule: RegulatoryRuleDTO,
        commodity_category: str = "packaged_commodity",
        net_quantity_g: Optional[float] = None,
        is_imported: bool = False,
        is_retail: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates whether a specific statutory rule applies to the package context.
        Returns:
            {
                "applicable": bool,
                "reason": str,
                "cross_regulatory_framework": Optional[str],
                "statutory_reference": str
            }
        """
        cat = (commodity_category or "packaged_commodity").lower().strip()
        raw_cats = getattr(rule, "applicable_categories", None) if hasattr(rule, "applicable_categories") else (getattr(rule, "applicable_product_categories", None) if hasattr(rule, "applicable_product_categories") else None)
        if not raw_cats:
            raw_cats = ["all"]
        rule_cats = [c.lower().strip() for c in raw_cats]

        # 1. Check wholesale / institutional package exemption under Rule 3
        if not is_retail or cat in cls.WHOLESALE_OR_INSTITUTIONAL:
            # Rule 3 exemption: provisions do not apply to packages containing commodity > 25kg or 25L (except cement/fertilizer) or packaged for institutional consumers
            if rule.rule_id not in ["PCR-R6-003", "PCR-R6-005"]:
                return {
                    "applicable": False,
                    "reason": "Exempted under Rule 3: Wholesale/Industrial/Institutional packaging provisions apply.",
                    "cross_regulatory_framework": None,
                    "statutory_reference": "Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 3"
                }

        # 2. Check small package threshold exemption under Rule 26 (< 10g or < 10ml)
        if net_quantity_g is not None and net_quantity_g < 10.0:
            if rule.rule_id in ["PCR-R6-001", "PCR-R6-002"]:  # Small packages exempt from certain declarations
                return {
                    "applicable": False,
                    "reason": f"Exempted under Rule 26: Net quantity ({net_quantity_g}g) is less than 10g small packaging threshold.",
                    "cross_regulatory_framework": None,
                    "statutory_reference": "Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 26"
                }

        # 3. Country of Origin applicability
        if rule.field_to_validate == "country_of_origin":
            return {
                "applicable": True,
                "reason": "Mandatory statutory declaration of Country of Origin under Rule 6(1)(m) (as amended 2017) for all packaged commodities.",
                "cross_regulatory_framework": "Department of Consumer Affairs Notification G.S.R. 629(E)",
                "statutory_reference": "Rule 6(1)(m)"
            }

        # 4. Food Product Cross-Regulatory Framework (Requirement 8)
        is_food = cat in cls.FOOD_CATEGORIES or "food" in cat
        if is_food:
            if rule.field_to_validate in ["date_of_manufacture", "expiry_date", "best_before"]:
                return {
                    "applicable": True,
                    "reason": "Cross-regulatory requirement: Date declaration governed concurrently by Legal Metrology Rule 6(1)(d) and FSSAI Packaging & Labelling Regulations.",
                    "cross_regulatory_framework": "FSSAI (Food Safety and Standards Act, 2006) read with Legal Metrology PCR Rule 6(1)(d)",
                    "statutory_reference": "Legal Metrology Rule 6(1)(d) & FSSAI Reg. 2.2.2"
                }
            elif rule.field_to_validate == "net_quantity":
                return {
                    "applicable": True,
                    "reason": "Statutory Net Quantity declaration with Schedule II metric unit constraints, cross-harmonized with FSSAI.",
                    "cross_regulatory_framework": "FSSAI Reg. 2.2.2(3) & Legal Metrology Schedule II",
                    "statutory_reference": "Rule 6(1)(c) & FSSAI Standards"
                }

        # 5. General category matching
        sec = getattr(rule, "section", None) if hasattr(rule, "section") else getattr(rule, "source_reference", "Rule 6")
        if "all" in rule_cats or "packaged_commodity" in rule_cats or cat in rule_cats:
            return {
                "applicable": True,
                "reason": f"Statutory requirement applicable to '{commodity_category}' under {sec}.",
                "cross_regulatory_framework": None,
                "statutory_reference": f"{sec} - Legal Metrology (Packaged Commodities) Rules, 2011"
            }

        return {
            "applicable": False,
            "reason": f"Rule restricted to categories {rule_cats}; does not apply to '{commodity_category}'.",
            "cross_regulatory_framework": None,
            "statutory_reference": sec
        }
