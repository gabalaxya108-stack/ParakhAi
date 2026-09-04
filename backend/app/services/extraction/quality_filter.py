import re
from typing import Optional, Tuple
from backend.app.schemas.ocr import OCRBlock
from backend.app.core.logging import get_logger

logger = get_logger("services.extraction.quality_filter")

STATUTORY_LABEL_REGEX = re.compile(
    r"\b(?:MAX(?:IMUM)?\s*RETAIL\s*PRICE|M\.?R\.?P\.?|NET\s*(?:QUANTITY|WT|WEIGHT|QTY)|"
    r"MFD\.?\s*(?:DATE)?|DATE\s*OF\s*(?:MFG|MANUFACTURE|PKG|PACKING)|PKD\.?\s*(?:DATE)?|"
    r"BATCH\s*(?:NO|NUMBER)|LOT\s*(?:NO|NUMBER)|B\.?\s*NO\.?|"
    r"CONSUMER\s*CARE|CUSTOMER\s*CARE|FOR\s*FEEDBACK|FEEDBACK@|"
    r"COUNTRY\s*OF\s*ORIGIN|MADE\s*IN|PRODUCT\s*OF|"
    r"MANUFACTURED\s*BY|MFD\.?\s*BY|PACKED\s*BY|PKD\.?\s*BY|IMPORTED\s*BY)\b",
    re.IGNORECASE
)

class DeclarationQualityFilter:
    """
    Perception filter and validator for Legal Metrology packaging declarations.
    Extracts, cleans, and bounds declarations across isolated and multi-line OCR blocks.
    """

    @classmethod
    def filter_mrp(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.95

        clean = re.sub(r"\s+", " ", raw)

        # Match price amounts: ₹60, ₹60.00, Rs. 60.00, Rs 60/-, 60.00
        price_match = re.search(r"(?:₹|Rs\.?|INR)?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)(?:\s*\/\-)?", clean, re.IGNORECASE)
        has_mrp_kw = bool(re.search(r"(?:mrp|max(?:imum)?\s*retail\s*price|retail\s*price|price)", clean, re.IGNORECASE))
        has_tax = bool(re.search(r"(?:incl(?:usive|\.)?\s*of\s*all\s*taxes|incl\.?\s*taxes|inclusive\s*of\s*taxes|all\s*taxes)", clean, re.IGNORECASE))

        if price_match:
            try:
                amt_str = price_match.group(1).replace(",", "")
                val_float = float(amt_str)
                if 0.5 <= val_float <= 500000.0:
                    clean_val = f"₹{val_float:.2f}"
                    if has_tax:
                        clean_val = f"₹{val_float:.2f} (Inclusive of all taxes)"
                    final_conf = conf
                    return "FOUND", clean_val, final_conf, raw
            except ValueError:
                pass

        if has_mrp_kw and not price_match:
            return "UNCLEAR", None, conf, raw

        return "NOT_FOUND", None, 0.0, None

    @classmethod
    def filter_net_quantity(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.95

        # Metric quantity: e.g. "200 g", "1.5 kg", "500 ml", "1 L", "200 gms"
        match = re.search(r"\b(\d+(?:\.\d+)?)\s*(g|kg|ml|l|ltr|gm|gms|grams|kgm|litres?|millilitres?)\b", raw, re.IGNORECASE)
        if match:
            num = match.group(1)
            raw_unit = match.group(2).lower()
            unit_map = {
                "g": "g", "gm": "g", "gms": "g", "grams": "g",
                "kg": "kg", "kgm": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
                "ml": "ml", "mls": "ml", "millilitre": "ml", "millilitres": "ml",
                "l": "l", "lt": "l", "ltr": "l", "litre": "l", "litres": "l"
            }
            clean_unit = unit_map.get(raw_unit, raw_unit)
            clean_val = f"{num} {clean_unit}"
            return "FOUND", clean_val, conf, raw

        # Count quantity: e.g. "10 N", "1 U", "5 Pieces"
        count_match = re.search(r"\b(\d+)\s*(?:N|U|Units?|Pieces?|Pcs?)\b", raw, re.IGNORECASE)
        if count_match:
            clean_val = f"{count_match.group(1)} N"
            return "FOUND", clean_val, conf, raw

        if re.search(r"(?:net\s*quantity|net\s*wt|net\s*qty|quantity)", raw, re.IGNORECASE):
            return "UNCLEAR", None, conf, raw

        return "NOT_FOUND", None, 0.0, None

    @classmethod
    def filter_manufacturer(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.92

        if len(raw) < 8 or re.search(r"^(?:Lot\s*No|LotN|MFD[:\.\s-]|USE\s*BY|EXPIRY|BATCH|PKD[:\.\s-]|BEST\s*BEFORE)", raw, re.IGNORECASE):
            return "NOT_FOUND", None, 0.0, None

        cleaned = re.sub(
            r"^(?:Manufactured\s*(?:&|and)?\s*Packed\s*By|Mfd\.?\s*(?:&|and)?\s*Pkd\.?\s*By|Manufactured\s*By|Marketed\s*By|Packed\s*By|Mfg\.?\s*By|Mit\.?\s*by\.?|Mig\.?\s*by\.?|Imported\s*By)[:\s-]*",
            "",
            raw,
            flags=re.IGNORECASE
        ).strip()
        cleaned = re.sub(r"^[\s\.,:\-]+", "", cleaned).strip()

        has_pin = bool(re.search(r"\b[1-9][0-9]{5}\b", raw))
        has_entity = any(re.search(rf"\b{e}\b", raw, re.IGNORECASE) for e in ["ltd", "limited", "pvt", "private", "foods", "industries", "works", "enterprises", "company", "co", "corp", "llp", "india", "nestle", "nestlé"])

        if (len(cleaned) >= 10 and (has_pin or has_entity)) or len(cleaned) >= 20:
            return "FOUND", cleaned, conf, raw

        if len(cleaned) >= 10:
            return "FOUND", cleaned, conf, raw

        return "UNCLEAR", None, conf, raw

    @classmethod
    def filter_consumer_care(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.95

        has_phone = bool(re.search(r"\b(1800[- ]?\d{3}[- ]?\d{3,4}|(?:\+91[- ]?)?[6-9]\d{9}|0\d{2,4}[- ]?\d{6,8})\b", raw))
        has_email = bool(re.search(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", raw))
        has_care_kw = bool(re.search(r"(?:consumer\s*care|customer\s*care|consumer\s*services|helpline|toll\s*free|wecare|feedback|contact\s*us|grievance|complaints)", raw, re.IGNORECASE))

        if has_phone or has_email or has_care_kw:
            cleaned = re.sub(r"^(?:Consumer\s*Care\s*(?:Helpline|Manager|Cell)?|Customer\s*Care|For\s*Feedback|Contact\s*Us)[:\s-]*", "", raw, flags=re.IGNORECASE).strip()
            return "FOUND", cleaned or raw, max(conf, 0.95), raw

        return "NOT_FOUND", None, 0.0, None

    @classmethod
    def filter_dates(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.95

        # Format DD/MM/YYYY or MM/YYYY
        date_match = re.search(r"\b([0-3]?[0-9][\/\-\.]0?[1-9]|1[0-2][\/\-\.]\d{2,4}|0?[1-9]|1[0-2][\/\-\.]20\d{2}|0?[1-9]|1[0-2][\/\-\.]\d{2})\b", raw)
        if date_match:
            return "FOUND", date_match.group(0), conf, raw

        month_match = re.search(r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*[\s\.-]+(20\d{2}|\d{2})\b", raw, re.IGNORECASE)
        if month_match:
            return "FOUND", f"{month_match.group(1).upper()} {month_match.group(2)}", conf, raw

        if re.search(r"(?:mfd|mfg|pkd|packed|date)", raw, re.IGNORECASE):
            return "UNCLEAR", None, conf, raw

        return "NOT_FOUND", None, 0.0, None

    @classmethod
    def filter_country_of_origin(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.95

        if re.search(r"\b(?:India|Bharat)\b", raw, re.IGNORECASE):
            return "FOUND", "India", conf, raw

        match = re.search(r"(?:Country of Origin|Made in|Product of|ORIGIN)[:\s-]*([A-Za-z\s]+)", raw, re.IGNORECASE)
        if match and len(match.group(1).strip()) >= 2:
            return "FOUND", match.group(1).strip().title(), max(conf, 0.95), raw

        return "NOT_FOUND", None, 0.0, None

    @classmethod
    def filter_batch_number(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.92

        if re.search(r"\b(?:Plot|Industrial|Area|House|Sector|Pvt|Ltd|Road|Street)\b", raw, re.IGNORECASE):
            return "NOT_FOUND", None, 0.0, None

        match = re.search(r"(?:Batch\s*(?:No\.?|Number)?|Lot\s*(?:No\.?|Number)?|B\.?\s*No\.?|BATCH)[:\s\.\-\|\}]*([A-Za-z0-9\/-]+)", raw, re.IGNORECASE)
        if match:
            clean_batch = match.group(1).strip()
            if clean_batch.upper() not in ["MFD", "EXP", "USE", "BY", "DATE", "NO", "NUMBER", "PLOT"] and len(clean_batch) >= 2:
                return "FOUND", clean_batch, max(conf, 0.95), raw

        return "NOT_FOUND", None, 0.0, None

    @classmethod
    def filter_product_name(cls, block_or_text: Optional[OCRBlock | str]) -> Tuple[str, Optional[str], float, Optional[str]]:
        if not block_or_text:
            return "NOT_FOUND", None, 0.0, None

        raw = block_or_text.text.strip() if isinstance(block_or_text, OCRBlock) else str(block_or_text).strip()
        conf = round(block_or_text.confidence, 2) if isinstance(block_or_text, OCRBlock) else 0.90

        if STATUTORY_LABEL_REGEX.search(raw):
            return "UNCLEAR", None, conf, raw

        disallowed = [
            r"World\s*Trade\s*Centre", r"Lic\.?\s*No", r"Registered\s*Office", r"Plot\s*No",
            r"Industrial\s*Area", r"Store\s*in", r"For\s*Sale\s*in", r"Nutritional",
            r"Ingredients", r"Consumer\s*Care", r"Max\.?\s*Retail"
        ]
        for dis in disallowed:
            if re.search(dis, raw, re.IGNORECASE):
                return "UNCLEAR", None, conf, raw

        if len(raw) >= 3:
            return "FOUND", raw, max(conf, 0.90), raw

        return "NOT_FOUND", None, 0.0, None
