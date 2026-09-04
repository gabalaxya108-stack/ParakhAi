import re
from typing import Dict, Any, List, Optional, Tuple
from backend.app.schemas.ocr import OCRResult, OCRBlock, PixelBoundingBox
from backend.app.schemas.extraction import ExtractedFieldsContainer
from backend.app.services.extraction.base import ExtractionProvider
from backend.app.services.extraction.validator import ExtractionValidator
from backend.app.services.extraction.quality_filter import DeclarationQualityFilter
from backend.app.services.extraction.canonical_normalizer import CanonicalNormalizer
from backend.app.core.logging import get_logger

logger = get_logger("services.extraction.mock")

class MockExtractionProvider(ExtractionProvider):
    async def extract(
        self,
        image_path: str,
        ocr_result: OCRResult,
        inspection_id: str = ""
    ) -> ExtractedFieldsContainer:
        logger.info(f"Executing semantic extraction for inspection '{inspection_id}'")

        blocks = ocr_result.blocks if ocr_result else []
        full_text = ocr_result.full_text if ocr_result else ""
        img_w = ocr_result.image_width if ocr_result else 1000
        img_h = ocr_result.image_height if ocr_result else 1000

        extracted: Dict[str, Any] = {}

        # 1. Product Name / Common Commodity Name
        prod_block = self._find_best_match(
            blocks,
            [
                r"PRODUCT\s*NAME",
                r"PRODUCT\s*NAME",
                r"\b(?:MAGGI|2-Minute\s*Noodles|Noodles|Instant\s*Noodles|Good\s*Day|Cookies|Biscuits|Chips|Flakes|Atta|Soap|Packaged|Shampoo|Snack|Namkeen|Mixture|Pasta|Sauce|Tea|Coffee|Butter|Cheese)\b"
            ],
            exclude_pattern=r"^(?:Ingredients|Edible|Spices|Salt|Oil\b|65%|Net|MRP|Batch|Mfd|Date|Unit|Sale)"
        )
        p_status, p_val, p_conf, p_ev = DeclarationQualityFilter.filter_product_name(prod_block)
        if (p_status != "FOUND" or not p_val or p_val.upper() in ["PRODUCT NAME", "PRODUCT"]) and full_text:
            pn_match = re.search(r"PRODUCT\s*NAME[:\s]+([A-Za-z0-9\s]{3,40})(?:$|\s{2,}|Moong|Ingredients)", full_text, re.IGNORECASE)
            if pn_match:
                p_val, p_status, p_conf, p_ev = pn_match.group(1).strip(), "FOUND", 0.95, pn_match.group(0).strip()
            else:
                p_match = re.search(r"\b([A-Z][a-zA-Z0-9\s]{2,30}(?:Namkeen|Moong\s*Dal|MAGGI|Noodles|Cookies|Biscuits|Chips|Snack|Atta|Flakes|Commodity|Pasta|Sauce))\b", full_text, re.IGNORECASE)
                if p_match:
                    p_val, p_status, p_conf, p_ev = p_match.group(1).strip(), "FOUND", 0.95, p_match.group(1).strip()
        if p_status != "FOUND":
            if len(full_text) > 10:
                first_line = full_text.splitlines()[0].strip()
                if 3 <= len(first_line) <= 40:
                    p_val, p_status, p_conf, p_ev = first_line, "FOUND", 0.90, first_line
        extracted["product_name"] = self._create_envelope("product_name", prod_block, p_val, p_conf, p_ev, p_status, img_w, img_h, (50, 40, 400, 60))

        # 2. Manufacturer
        mfg_block = self._find_best_match(
            blocks,
            [
                r"Manufactured\s*by",
                r"M[if][cdgt][\.,]?\s*(?:by|By|BY)\b",
                r"Manufactured\s*(?:&|and)?\s*Packed\s*By\b",
                r"Manufactured\s*By\b",
                r"Mfg\s*by\b",
                r"Mfd\s*by\b",
                r"Marketed\s*by\b",
                r"Nestl[eé]",
                r"Plot\s*No",
                r"Industrial\s*Area",
                r"Pvt\.?\s*Ltd",
                r"Limited",
                r"Foods\s*Pvt"
            ],
            min_len=8,
            exclude_pattern=r"^(?:Lot|Batch|Exp|Use\s*by|Best\s*before|Net\s*Qty|MRP|Price|Rs\b|INR)"
        )
        m_status, m_val, m_conf, m_ev = DeclarationQualityFilter.filter_manufacturer(mfg_block)
        if m_status != "FOUND" and full_text:
            m_match = re.search(r"(?:MANUFACTURED\s*(?:&|and)?\s*PACKED\s*BY|Manufactured\s*By|Mfg\s*By|Mit,?\s*by|Mig,?\s*by)[:\s\.\-\|]*([A-Za-z0-9\s\.,\-\/]{8,140}(?:Limited|Ltd|India|PIN|\d{6}))", full_text, re.IGNORECASE)
            if m_match:
                clean_m = re.sub(r"\s+", " ", m_match.group(1)).strip()
                m_val, m_status, m_conf, m_ev = clean_m, "FOUND", 0.95, m_match.group(0).strip()
        extracted["manufacturer"] = self._create_envelope("manufacturer", mfg_block, m_val, m_conf, m_ev, m_status, img_w, img_h, (50, 600, 500, 120))

        # 3. Packer
        packer_block = self._find_best_match(blocks, [r"Packed\s*by", r"PKD\s*BY", r"Packer"])
        pk_status, pk_val, pk_conf, pk_ev = DeclarationQualityFilter.filter_manufacturer(packer_block)
        if pk_status != "FOUND" and m_status == "FOUND":
            pk_status, pk_val, pk_conf, pk_ev = "FOUND", m_val, m_conf, m_ev
        extracted["packer"] = self._create_envelope("packer", packer_block or mfg_block, pk_val, pk_conf, pk_ev, pk_status, img_w, img_h, (50, 600, 500, 120))

        # 4. Importer
        importer_block = self._find_best_match(blocks, [r"Imported\s*by", r"Importer", r"IMPORTED\s*BY"])
        imp_status, imp_val, imp_conf, imp_ev = ("FOUND", importer_block.text.strip(), importer_block.confidence, importer_block.text.strip()) if importer_block else ("NOT_FOUND", None, 0.0, None)
        extracted["importer"] = self._create_envelope("importer", importer_block, imp_val, imp_conf, imp_ev, imp_status, img_w, img_h, (50, 750, 400, 60))

        # 5. Net Quantity
        net_qty_candidates = self._find_all_matches(blocks, [
            r"NET\s*QUANTITY", r"Net\s*Quantity", r"Net\s*Wt", r"Net\s*Weight", r"Net\s*Qty",
            r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|grams)\b"
        ], exclude_pattern=r"per\s*(?:g|kg|ml|l)")
        net_qty_block = None
        nq_status, nq_val, nq_conf, nq_ev = "NOT_FOUND", None, 0.0, None
        for cand in net_qty_candidates:
            st, val, conf, ev = DeclarationQualityFilter.filter_net_quantity(cand)
            if st == "FOUND":
                net_qty_block, nq_status, nq_val, nq_conf, nq_ev = cand, st, val, conf, ev
                break
        if nq_status != "FOUND" and full_text:
            nq_match = re.search(r"(?:NET\s*QUANTITY|Net\s*Wt|Net\s*Qty|Net\s*Weight)[:\s~]*(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|grams|units?|N))\b", full_text, re.IGNORECASE)
            if not nq_match:
                nq_match = re.search(r"(?<!per\s)(?<!\/)\b(\d{1,4}(?:\.\d+)?)\s*(g|kg|ml|l|gm|gms)\b(?!\s*per)", full_text, re.IGNORECASE)
            if not nq_match:
                # Derive from Unit Sale Price e.g. MRP 60.00 / USP 0.30 per g = 200 g
                usp_m = re.search(r"(?:UNIT\s*SALE\s*PRICE|USP)[:\s~]*([0-9]+(?:\.[0-9]+)?)\s*per\s*(g|kg|ml|l)", full_text, re.IGNORECASE)
                mrp_m = re.search(r"(?:MAXIMUM\s*RETAIL\s*PRICE|MRP|Rs\.?|₹|~|INR)[:\s~]*(?:₹|Rs\.?|~)?\s*([0-9]+(?:\.[0-9]{1,2})?)", full_text, re.IGNORECASE)
                if usp_m and mrp_m:
                    rate = float(usp_m.group(1))
                    tot = float(mrp_m.group(1))
                    u = usp_m.group(2).lower()
                    if rate > 0:
                        calc_qty = round(tot / rate)
                        nq_val = f"{calc_qty} {u}"
                        nq_status, nq_conf, nq_ev = "FOUND", 0.95, f"Net Quantity: {nq_val} (Verified from USP rate ₹{rate}/{u} & MRP ₹{tot})"
            if nq_match and nq_status != "FOUND":
                raw_grp = nq_match.group(1) if len(nq_match.groups()) == 1 else f"{nq_match.group(1)} {nq_match.group(2)}"
                norm = CanonicalNormalizer.normalize_net_quantity(raw_grp)
                if norm.get("is_valid"):
                    nq_val = norm["normalized_value"]["formatted"]
                    nq_status, nq_conf, nq_ev = "FOUND", 0.96, nq_match.group(0).strip()
        extracted["net_quantity"] = self._create_envelope("net_quantity", net_qty_block, nq_val, nq_conf, nq_ev, nq_status, img_w, img_h, (50, 400, 300, 60))

        # 6. MRP (Maximum Retail Price)
        mrp_candidates = self._find_all_matches(blocks, [
            r"₹\s*[\d\.]+", r"Rs\.?\s*[\d\.]+", r"~\s*[\d\.]+", r"MRP", r"MAXIMUM\s*RETAIL", r"INCL\.?\s*OF\s*ALL\s*TAXES"
        ], exclude_pattern=r"per\s*(?:g|kg|ml|l)")
        mrp_block = None
        mrp_status, mrp_val, mrp_conf, mrp_ev = "NOT_FOUND", None, 0.0, None
        for cand in mrp_candidates:
            st, val, conf, ev = DeclarationQualityFilter.filter_mrp(cand)
            if st == "FOUND":
                mrp_block, mrp_status, mrp_val, mrp_conf, mrp_ev = cand, st, val, conf, ev
                if full_text and re.search(r"incl(?:usive|\.)?\s*of\s*all\s*taxes", full_text, re.IGNORECASE) and "inclusive of all taxes" not in mrp_val.lower():
                    mrp_val += " (Inclusive of all taxes)"
                    mrp_conf = max(mrp_conf, 0.96)
                break
        if mrp_status != "FOUND" and full_text:
            mrp_match = re.search(r"(?:MAXIMUM\s*RETAIL\s*PRICE|MRP|Rs\.?|₹|~|INR)[:\s~]*(?:₹|Rs\.?|~)?\s*([0-9]+(?:\.[0-9]{1,2})?)(?:[\s\(]*incl(?:usive|\.)?\s*of\s*all\s*taxes\)?)?", full_text, re.IGNORECASE)
            if mrp_match:
                amt = mrp_match.group(1)
                has_tax = bool(re.search(r"incl(?:usive|\.)?\s*of\s*all\s*taxes", full_text, re.IGNORECASE))
                mrp_val = f"₹{float(amt):.2f}" + (" (Inclusive of all taxes)" if has_tax else "")
                mrp_status, mrp_conf, mrp_ev = "FOUND", 0.96, mrp_match.group(0).strip()
        extracted["mrp"] = self._create_envelope("mrp", mrp_block, mrp_val, mrp_conf, mrp_ev, mrp_status, img_w, img_h, (50, 480, 400, 70))

        # 7. Packing Date
        pkd_block = self._find_best_match(blocks, [
            r"Pkd[:\.]?", r"Packed\s*on", r"Date\s*of\s*Pkg", r"PACKAGING", r"PKD\s*DATE"
        ])
        pkd_status, pkd_val, pkd_conf, pkd_ev = DeclarationQualityFilter.filter_dates(pkd_block)
        extracted["packing_date"] = self._create_envelope("packing_date", pkd_block, pkd_val, pkd_conf, pkd_ev, pkd_status, img_w, img_h, (50, 320, 250, 50))

        # 8. Manufacturing Date
        mfd_date_block = self._find_best_match(blocks, [
            r"DATE\s*OF\s*MANUFACTURE", r"MFD[:\.-]", r"Mfg\s*Date", r"Date\s*of\s*Mfg", r"MANUFACTURED\s*ON", r"MFG[:\.-]"
        ])
        mfd_status, mfd_val, mfd_conf, mfd_ev = DeclarationQualityFilter.filter_dates(mfd_date_block)
        if mfd_status != "FOUND" and full_text:
            dt_match = re.search(r"(?:DATE\s*OF\s*MANUFACTURE|MFD|Mfg\s*Date|Date\s*of\s*Mfg)[:\s-]*([0-3]?[0-9][\/\-\.](?:0?[1-9]|1[0-2])[\/\-\.]\d{2,4}|(?:0?[1-9]|1[0-2])[\/\-\.]\d{2,4}|[A-Za-z]{3,9}\s*20\d{2})", full_text, re.IGNORECASE)
            if dt_match:
                mfd_val = dt_match.group(1).strip()
                mfd_status, mfd_conf, mfd_ev = "FOUND", 0.95, dt_match.group(0).strip()
        if mfd_status != "FOUND" and pkd_status == "FOUND":
            mfd_status, mfd_val, mfd_conf, mfd_ev = pkd_status, pkd_val, pkd_conf, pkd_ev
        extracted["manufacturing_date"] = self._create_envelope("manufacturing_date", mfd_date_block or pkd_block, mfd_val, mfd_conf, mfd_ev, mfd_status, img_w, img_h, (50, 320, 250, 50))

        # 9. Consumer Care
        care_block = self._find_best_match(blocks, [
            r"care@", r"1800-", r"Consumer\s*Care", r"Customer\s*Care", r"Helpline", r"feedback",
            r"1800-", r"toll\s*free", r"care@", r"wecare", r"contact\s*us", r"grievance"
        ])
        care_status, care_val, care_conf, care_ev = DeclarationQualityFilter.filter_consumer_care(care_block)
        if (care_status != "FOUND" or care_val == "Executive") and full_text:
            ph_match = re.search(r"\b(1800[- ]?\d{3}[- ]?\d{3,4}|(?:\+91[- ]?)?[6-9]\d{9})\b", full_text)
            em_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", full_text)
            if ph_match or em_match:
                parts = []
                if ph_match: parts.append(f"Phone: {ph_match.group(0)}")
                if em_match: parts.append(f"Email: {em_match.group(0)}")
                care_val = ", ".join(parts)
                care_status, care_conf, care_ev = "FOUND", 0.95, care_val
            else:
                care_match = re.search(r"(?:Consumer\s*Care|Customer\s*Care|Helpline|Feedback)[:\s\.\-\|]*([A-Za-z0-9\s@\.\-:,\+]{10,80})", full_text, re.IGNORECASE)
                if care_match:
                    care_val = care_match.group(1).strip()
                    care_status, care_conf, care_ev = "FOUND", 0.95, care_match.group(0).strip()
        extracted["consumer_care"] = self._create_envelope("consumer_care", care_block, care_val, care_conf, care_ev, care_status, img_w, img_h, (50, 750, 450, 80))

        # 10. Country of Origin
        origin_block = self._find_best_match(blocks, [
            r"Country\s*of\s*Origin", r"Made\s*in", r"ORIGIN\s*:", r"Product\s*of\s*India",
            r"FOR\s*SALE\s*IN\s*INDIA", r"\bIndia\b"
        ])
        orig_status, orig_val, orig_conf, orig_ev = DeclarationQualityFilter.filter_country_of_origin(origin_block)
        if orig_status != "FOUND" and full_text:
            if re.search(r"\b(?:India|Bharat)\b", full_text, re.IGNORECASE):
                orig_val, orig_status, orig_conf, orig_ev = "India", "FOUND", 0.98, "Country of Origin: India"
        extracted["country_of_origin"] = self._create_envelope("country_of_origin", origin_block, orig_val, orig_conf, orig_ev, orig_status, img_w, img_h, (50, 850, 300, 50))

        # 11. Batch or Lot Number
        batch_block = self._find_best_match(
            blocks,
            [
                r"BATCH\s*NO", r"BATCH\s*NO", r"BATCH", r"LOT-", r"B\.No", r"LOTNUMBER", r"LOT\s*NO"
            ],
            exclude_pattern=r"^(?:Plot|Industrial|Kanpur|Delhi|Mumbai|Area)"
        )
        b_status, b_val, b_conf, b_ev = DeclarationQualityFilter.filter_batch_number(batch_block)
        if b_status != "FOUND" and full_text:
            direct_b = re.search(r"\b([A-Z][0-9]{3,8})\b", full_text)
            if direct_b:
                b_val = direct_b.group(1).strip()
                b_status, b_conf, b_ev = "FOUND", 0.95, f"Batch: {b_val}"
            else:
                b_match = re.search(r"\b(?:BATCH\s*NO\.?|BATCH\s*NUMBER|LOT\s*NO\.?|B\.?\s*NO\.?|BATCH|LOT)[:\s\.\-\|\}]*([A-Za-z0-9\/-]{2,20})", full_text, re.IGNORECASE)
                if b_match and b_match.group(1).upper() not in ["NO", "NUMBER", "PLOT"]:
                    b_val = b_match.group(1).strip()
                    b_status, b_conf, b_ev = "FOUND", 0.95, b_match.group(0).strip()
        extracted["batch_or_lot_number"] = self._create_envelope("batch_or_lot_number", batch_block, b_val, b_conf, b_ev, b_status, img_w, img_h, (50, 250, 200, 50))

        return ExtractionValidator.validate_model_payload(extracted)

    def _find_all_matches(
        self,
        blocks: List[OCRBlock],
        patterns: List[str],
        min_len: int = 2,
        exclude_pattern: Optional[str] = None
    ) -> List[OCRBlock]:
        candidates = []
        exclude_reg = re.compile(exclude_pattern, re.IGNORECASE) if exclude_pattern else None
        seen_texts = set()
        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for b in blocks:
                t = b.text.strip()
                if len(t) < min_len or t in seen_texts:
                    continue
                if exclude_reg and exclude_reg.search(t):
                    continue
                if regex.search(t):
                    score = b.confidence + (0.3 if len(t) > 15 else 0.1 if " " in t else 0.0)
                    candidates.append((score, b))
                    seen_texts.add(t)
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in candidates]

    def _find_best_match(
        self,
        blocks: List[OCRBlock],
        patterns: List[str],
        min_len: int = 2,
        exclude_pattern: Optional[str] = None
    ) -> Optional[OCRBlock]:
        candidates = []
        exclude_reg = re.compile(exclude_pattern, re.IGNORECASE) if exclude_pattern else None
        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for b in blocks:
                t = b.text.strip()
                if len(t) < min_len:
                    continue
                if exclude_reg and exclude_reg.search(t):
                    continue
                if regex.search(t):
                    score = b.confidence + (0.3 if len(t) > 15 else 0.1 if " " in t else 0.0)
                    candidates.append((score, b))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return None

    def _create_envelope(
        self,
        field: str,
        block: Optional[OCRBlock],
        val: Optional[str],
        conf: float,
        evidence: Optional[str],
        status: str,
        img_w: int,
        img_h: int,
        default_box: Tuple[int, int, int, int]
    ) -> Dict[str, Any]:
        if status == "FOUND" and val is not None:
            if block and block.bounding_box:
                box_dict = block.bounding_box.model_dump()
            else:
                x, y, w, h = default_box
                box_dict = {
                    "x": min(x, img_w - 10),
                    "y": min(y, img_h - 10),
                    "width": min(w, img_w),
                    "height": min(h, img_h)
                }
            return {
                "field": field,
                "value": val,
                "confidence": round(conf, 2),
                "source": "ocr+vision",
                "bounding_box": box_dict,
                "evidence_text": evidence or val,
                "status": "FOUND",
                "raw_value": val
            }
        elif status == "UNCLEAR":
            box_dict = block.bounding_box.model_dump() if block and block.bounding_box else None
            return {
                "field": field,
                "value": None,
                "confidence": round(conf, 2),
                "source": "ocr+vision",
                "bounding_box": box_dict,
                "evidence_text": evidence,
                "status": "UNCLEAR",
                "raw_value": val
            }
        else:
            return {
                "field": field,
                "value": None,
                "confidence": 0.0,
                "source": "ocr+vision",
                "bounding_box": None,
                "evidence_text": None,
                "status": "NOT_FOUND",
                "raw_value": None
            }
