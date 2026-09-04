import re
from typing import Dict, Any, Optional, Tuple

class CanonicalNormalizer:
    """
    Semantic Normalizer for Legal Metrology mandatory packaging declarations.
    Converts raw OCR and Vision perception outputs into canonical structured data objects,
    handling semantic variations, OCR character substitutions, whitespace, units, dates,
    and statutory tax-inclusive formulations.
    """

    @classmethod
    def normalize_field(cls, field_name: str, raw_text: Optional[str]) -> Dict[str, Any]:
        """Dispatches normalization based on declaration field name."""
        if not raw_text or not str(raw_text).strip():
            return {
                "field": field_name,
                "raw_value": None,
                "normalized_value": None,
                "is_valid": False,
                "status": "NOT_FOUND"
            }

        text = str(raw_text).strip()
        field_lower = field_name.lower().strip()

        if field_lower in ["mrp", "retail_price", "price", "maximum_retail_price"]:
            return cls.normalize_mrp(text)
        elif field_lower in ["net_quantity", "net_weight", "net_qty", "quantity"]:
            return cls.normalize_net_quantity(text)
        elif field_lower in ["manufacturing_date", "mfg_date", "packing_date", "date", "date_of_manufacture"]:
            return cls.normalize_date(text)
        elif field_lower in ["manufacturer", "packer", "importer", "manufacturer_packer"]:
            return cls.normalize_manufacturer(text)
        elif field_lower in ["consumer_care", "customer_care", "helpline", "consumer_complaints"]:
            return cls.normalize_consumer_care(text)
        elif field_lower in ["country_of_origin", "origin"]:
            return cls.normalize_origin(text)
        elif field_lower in ["batch_or_lot_number", "batch_number", "lot_number", "batch_no"]:
            return cls.normalize_batch_number(text)
        elif field_lower in ["product_name", "generic_name", "common_name"]:
            return cls.normalize_product_name(text)
        else:
            return {
                "field": field_name,
                "raw_value": text,
                "normalized_value": text,
                "is_valid": True,
                "status": "FOUND"
            }

    @classmethod
    def normalize_product_name(cls, text: str) -> Dict[str, Any]:
        """Normalizes Generic or Common Product Name."""
        clean_text = re.sub(r"\s+", " ", text).strip()
        clean_text = re.sub(r"^(?:Product\s*(?:Name)?|Generic\s*Name|Common\s*Name|Commodity)[:\s-]*", "", clean_text, flags=re.IGNORECASE).strip()
        is_valid = len(clean_text) >= 2
        return {
            "field": "product_name",
            "raw_value": text,
            "normalized_value": clean_text,
            "is_valid": is_valid,
            "status": "FOUND" if is_valid else "NOT_FOUND"
        }

    @classmethod
    def normalize_mrp(cls, text: str) -> Dict[str, Any]:
        """
        Normalizes MRP declaration:
        - Extracts numeric amount (float)
        - Detects currency symbol/code (INR, Rs, ₹)
        - Detects statutory tax-inclusive phrase
        """
        clean_text = re.sub(r"\s+", " ", text).strip()

        # Extract numeric value: ₹60, ₹60.00, Rs. 60.00, Rs 60/-, 60.00, 1,200.50
        amount_match = re.search(r"(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)(?:\s*/-)?", clean_text, re.IGNORECASE)
        amount: Optional[float] = None
        if amount_match:
            try:
                raw_amt = amount_match.group(1).replace(",", "")
                amount = float(raw_amt)
            except Exception:
                amount = None

        # Check for statutory tax inclusive wording
        tax_patterns = [
            r"incl(?:usive|\.)?\s*of\s*all\s*taxes",
            r"incl(?:usive|\.)?\s*all\s*taxes",
            r"incl\.?\s*taxes",
            r"inclusive\s*of\s*taxes",
            r"all\s*taxes\s*incl(?:uded|\.)?",
            r"\(incl\.\s*of\s*all\s*taxes\)",
            r"\(inclusive\s*of\s*all\s*taxes\)"
        ]
        has_tax_inclusive = any(re.search(p, clean_text, re.IGNORECASE) for p in tax_patterns)

        # Detect Unit Sale Price (USP) if present in raw string
        usp_match = re.search(r"(?:usp|unit\s*sale\s*price)[:\s]*(?:₹|rs\.?)?\s*([0-9\.]+)\s*(?:per|\/)\s*([a-zA-Z]+)", clean_text, re.IGNORECASE)
        usp_val = None
        if usp_match:
            try:
                usp_val = f"₹{float(usp_match.group(1)):.2f} / {usp_match.group(2).lower()}"
            except Exception:
                pass

        formatted = f"₹{amount:.2f}" if amount is not None else clean_text
        if has_tax_inclusive:
            formatted_full = f"{formatted} (Inclusive of all taxes)"
        else:
            formatted_full = formatted

        return {
            "field": "mrp",
            "raw_value": text,
            "normalized_value": {
                "amount": amount,
                "currency": "INR",
                "tax_inclusive": has_tax_inclusive,
                "has_tax_inclusive_wording": has_tax_inclusive,
                "unit_sale_price": usp_val,
                "formatted": formatted_full,
                "price_string": formatted
            },
            "is_valid": amount is not None and amount > 0,
            "status": "FOUND" if amount is not None else "UNCLEAR"
        }

    @classmethod
    def normalize_net_quantity(cls, text: str) -> Dict[str, Any]:
        """
        Normalizes Net Quantity:
        - Extracts numeric magnitude and unit symbol
        - Maps units to canonical SI symbols (g, kg, ml, l, N, U)
        - Detects non-standard units (e.g. gms, kgs, mls) under Rule 11
        """
        clean_text = re.sub(r"\s+", " ", text).strip()

        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)", clean_text)
        magnitude: Optional[float] = None
        raw_unit: Optional[str] = None
        canonical_unit: Optional[str] = None
        is_standard_metric: bool = True

        if match:
            try:
                magnitude = float(match.group(1))
            except Exception:
                magnitude = None
            raw_unit = match.group(2).lower()

            unit_map = {
                "g": ("g", True),
                "gm": ("g", False),
                "gms": ("g", False),
                "gram": ("g", False),
                "grams": ("g", False),
                "kg": ("kg", True),
                "kgs": ("kg", False),
                "kilo": ("kg", False),
                "kilos": ("kg", False),
                "kilogram": ("kg", False),
                "kilograms": ("kg", False),
                "ml": ("ml", True),
                "mls": ("ml", False),
                "millilitre": ("ml", False),
                "millilitres": ("ml", False),
                "l": ("l", True),
                "lt": ("l", True),
                "ltr": ("l", False),
                "ltrs": ("l", False),
                "litre": ("l", False),
                "litres": ("l", False),
                "n": ("N", True),
                "u": ("U", True),
                "unit": ("U", True),
                "units": ("U", True),
                "pieces": ("U", False),
                "pcs": ("U", False)
            }

            if raw_unit in unit_map:
                canonical_unit, is_standard_metric = unit_map[raw_unit]
            else:
                canonical_unit = raw_unit

        weight_in_base_units: Optional[float] = None
        if magnitude is not None and canonical_unit:
            if canonical_unit == "g":
                weight_in_base_units = magnitude
            elif canonical_unit == "kg":
                weight_in_base_units = magnitude * 1000.0
            elif canonical_unit == "ml":
                weight_in_base_units = magnitude
            elif canonical_unit == "l":
                weight_in_base_units = magnitude * 1000.0

        formatted = f"{magnitude:g} {canonical_unit or raw_unit}" if magnitude is not None else clean_text

        return {
            "field": "net_quantity",
            "raw_value": text,
            "normalized_value": {
                "magnitude": magnitude,
                "raw_unit": raw_unit,
                "canonical_unit": canonical_unit,
                "is_standard_metric_symbol": is_standard_metric,
                "weight_in_grams_or_ml": weight_in_base_units,
                "formatted": formatted
            },
            "is_valid": magnitude is not None and canonical_unit is not None,
            "status": "FOUND" if magnitude is not None else "UNCLEAR"
        }

    @classmethod
    def normalize_date(cls, text: str) -> Dict[str, Any]:
        """
        Normalizes Date of Manufacture / Packing:
        - Resolves month & year (MM/YYYY)
        - Handles formats: 05/2024, 05/24, May 2024, 01/05/2024, 01-05-2024
        """
        clean_text = re.sub(r"\s+", " ", text).strip()

        month: Optional[int] = None
        year: Optional[int] = None
        day: Optional[int] = None

        month_names = {
            "jan": 1, "january": 1, "feb": 2, "february": 2,
            "mar": 3, "march": 3, "apr": 4, "april": 4,
            "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "august": 8, "sep": 9, "september": 9,
            "oct": 10, "october": 10, "nov": 11, "november": 11,
            "dec": 12, "december": 12
        }

        # Format: DD/MM/YYYY or DD-MM-YYYY
        d_match = re.search(r"\b([0-3]?[0-9])[\/\-\.]0?([1-9]|1[0-2])[\/\-\.]((?:20|19)[0-9]{2})\b", clean_text)
        if d_match:
            day = int(d_match.group(1))
            month = int(d_match.group(2))
            year = int(d_match.group(3))
        else:
            m_match = re.search(r"\b0?([1-9]|1[0-2])[\/\-\.]((?:20|19)[0-9]{2}|[2-3][0-9])\b", clean_text)
            if m_match:
                month = int(m_match.group(1))
                yr_val = int(m_match.group(2))
                year = yr_val if yr_val > 100 else 2000 + yr_val
            else:
                for m_name, m_num in month_names.items():
                    named_match = re.search(rf"\b{m_name}\b[,\s\.\-]*(\d{{4}}|\d{{2}})", clean_text, re.IGNORECASE)
                    if named_match:
                        month = m_num
                        yr_val = int(named_match.group(1))
                        year = yr_val if yr_val > 100 else 2000 + yr_val
                        break

        is_valid = month is not None and year is not None and 1 <= month <= 12
        formatted = f"{day:02d}/{month:02d}/{year}" if day and is_valid else (f"{month:02d}/{year}" if is_valid else clean_text)

        return {
            "field": "manufacturing_date",
            "raw_value": text,
            "normalized_value": {
                "day": day,
                "month": month,
                "year": year,
                "formatted": formatted if is_valid else clean_text
            },
            "is_valid": is_valid,
            "status": "FOUND" if is_valid else "UNCLEAR"
        }

    @classmethod
    def normalize_manufacturer(cls, text: str) -> Dict[str, Any]:
        """
        Normalizes Manufacturer / Packer details:
        - Extracts corporate identity
        - Detects address indicators and postal PIN code
        """
        clean_text = re.sub(r"\s+", " ", text).strip()
        stripped = re.sub(
            r"^(?:Manufactured\s*(?:&|and)\s*Packed\s*By|Mfd\.?\s*(?:&|and)?\s*Pkd\.?\s*By|Manufactured\s*By|Marketed\s*By|Packed\s*By|Imported\s*By|Mfg\s*By)[:\s-]*",
            "",
            clean_text,
            flags=re.IGNORECASE
        ).strip()

        pin_match = re.search(r"\b[1-9][0-9]{5}\b", clean_text)
        pin_code = pin_match.group(0) if pin_match else None

        has_entity_name = any(re.search(rf"\b{e}\b", clean_text, re.IGNORECASE) for e in ["ltd", "limited", "pvt", "private", "foods", "industries", "works", "enterprises", "company", "co", "corp", "llp"])
        has_substantial_address = len(stripped) >= 10 and (pin_code is not None or has_entity_name or len(stripped) >= 20)

        return {
            "field": "manufacturer",
            "raw_value": text,
            "normalized_value": {
                "full_address": stripped or clean_text,
                "pin_code": pin_code,
                "has_entity_name": has_entity_name,
                "has_complete_address": has_substantial_address
            },
            "is_valid": has_substantial_address or len(stripped) >= 5,
            "status": "FOUND" if (has_substantial_address or len(stripped) >= 5) else ("UNCLEAR" if len(clean_text) > 3 else "NOT_FOUND")
        }

    @classmethod
    def normalize_consumer_care(cls, text: str) -> Dict[str, Any]:
        """
        Normalizes Consumer Care grievance redressal:
        - Extracts phone / toll-free number
        - Extracts email address
        """
        clean_text = re.sub(r"\s+", " ", text).strip()

        phone_match = re.search(r"(?:1800[- ]?[0-9]{3}[- ]?[0-9]{3,4}|(?:\+91[- ]?)?[6-9][0-9]{9}|\b0[0-9]{2,4}[- ]?[0-9]{6,8}\b)", clean_text)
        phone = phone_match.group(0) if phone_match else None

        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", clean_text)
        email = email_match.group(0) if email_match else None

        has_executive = any(re.search(rf"\b{k}\b", clean_text, re.IGNORECASE) for k in ["executive", "officer", "manager", "care", "helpline", "cell", "in-charge", "grievance", "complaints", "feedback", "customer"])
        is_valid = phone is not None or email is not None or has_executive or len(clean_text) >= 10

        return {
            "field": "consumer_care",
            "raw_value": text,
            "normalized_value": {
                "phone": phone,
                "email": email,
                "has_executive_designation": has_executive,
                "raw_details": clean_text
            },
            "is_valid": is_valid,
            "status": "FOUND" if is_valid else ("UNCLEAR" if len(clean_text) > 3 else "NOT_FOUND")
        }

    @classmethod
    def normalize_origin(cls, text: str) -> Dict[str, Any]:
        """Normalizes Country of Origin declaration."""
        clean_text = re.sub(r"\s+", " ", text).strip().upper()
        is_india = "INDIA" in clean_text or "IND" in clean_text or "BHARAT" in clean_text
        country = "India" if is_india else clean_text.title()

        return {
            "field": "country_of_origin",
            "raw_value": text,
            "normalized_value": {
                "country": country,
                "is_domestic": is_india
            },
            "is_valid": len(clean_text) >= 2,
            "status": "FOUND" if len(clean_text) >= 2 else "NOT_FOUND"
        }

    @classmethod
    def normalize_batch_number(cls, text: str) -> Dict[str, Any]:
        """Normalizes Batch or Lot Number declaration."""
        clean_text = re.sub(r"\s+", " ", text).strip()
        cleaned_val = re.sub(r"^(?:batch\s*(?:no\.?)?|lot\s*(?:no\.?)?|b\.?\s*no\.?|code)[:\s\-]*", "", clean_text, flags=re.IGNORECASE).strip()

        return {
            "field": "batch_or_lot_number",
            "raw_value": text,
            "normalized_value": {
                "batch_code": cleaned_val or clean_text
            },
            "is_valid": len(cleaned_val or clean_text) >= 1,
            "status": "FOUND" if len(cleaned_val or clean_text) >= 1 else "NOT_FOUND"
        }
