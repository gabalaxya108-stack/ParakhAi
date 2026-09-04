import re
from typing import Tuple, Dict, Any, List, Optional
from backend.app.schemas.extraction import (
    ExtractedFieldsContainer,
    FieldExtractionResult,
    CandidateObservation,
    ReconciliationDetail
)
from backend.app.services.extraction.validator import REQUIRED_DECLARATION_FIELDS
from backend.app.services.extraction.canonical_normalizer import CanonicalNormalizer
from backend.app.core.logging import get_logger

logger = get_logger("services.extraction.reconciliation")

STATUTORY_LABEL_REGEX = re.compile(
    r"(?:MAX(?:IMUM)?\s*RETAIL\s*PRICE|M\.?R\.?P\.?|NET\s*(?:QUANTITY|WT|WEIGHT|QTY)|"
    r"MFD\.?\s*(?:DATE)?|DATE\s*OF\s*(?:MFG|MANUFACTURE|PKG|PACKING)|PKD\.?\s*(?:DATE)?|"
    r"BATCH\s*(?:NO|NUMBER)|LOT\s*(?:NO|NUMBER)|B\.?\s*NO\.?|"
    r"CONSUMER\s*CARE|CUSTOMER\s*CARE|FOR\s*FEEDBACK|FEEDBACK@|"
    r"COUNTRY\s*OF\s*ORIGIN|MADE\s*IN|PRODUCT\s*OF|"
    r"MANUFACTURED\s*BY|MFD\.?\s*BY|PACKED\s*BY|PKD\.?\s*BY|IMPORTED\s*BY)",
    re.IGNORECASE
)

class ExtractionReconciler:
    """
    Evidence-First Multi-Source Perception Reconciler:
    Combines Qwen Vision and Tesseract OCR into a single grounded declaration envelope.
    Separates extraction uncertainty from statutory evaluation.
    """

    @classmethod
    def _clean_str(cls, val: Optional[str]) -> str:
        if not val:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", str(val).lower().strip())

    @classmethod
    def _is_equivalent(cls, val_a: Optional[str], val_b: Optional[str], field_name: str) -> bool:
        if not val_a or not val_b:
            return False

        norm_a = cls._clean_str(val_a)
        norm_b = cls._clean_str(val_b)

        if norm_a == norm_b:
            return True

        # Field-specific semantic equivalences
        if field_name in ["mrp", "retail_price"]:
            m_a = re.findall(r"\d+(?:\.\d+)?", str(val_a))
            m_b = re.findall(r"\d+(?:\.\d+)?", str(val_b))
            if m_a and m_b and float(m_a[0]) == float(m_b[0]):
                return True

        if field_name == "net_quantity":
            n_a = CanonicalNormalizer.normalize_net_quantity(str(val_a))
            n_b = CanonicalNormalizer.normalize_net_quantity(str(val_b))
            if n_a.get("is_valid") and n_b.get("is_valid"):
                v_a = n_a["normalized_value"]
                v_b = n_b["normalized_value"]
                if v_a.get("magnitude") == v_b.get("magnitude") and v_a.get("canonical_unit") == v_b.get("canonical_unit"):
                    return True

        if field_name in ["manufacturing_date", "packing_date"]:
            d_a = CanonicalNormalizer.normalize_date(str(val_a))
            d_b = CanonicalNormalizer.normalize_date(str(val_b))
            if d_a.get("is_valid") and d_b.get("is_valid"):
                v_a = d_a["normalized_value"]
                v_b = d_b["normalized_value"]
                if v_a.get("month") == v_b.get("month") and v_a.get("year") == v_b.get("year"):
                    return True

        if field_name == "country_of_origin":
            o_a = CanonicalNormalizer.normalize_origin(str(val_a))
            o_b = CanonicalNormalizer.normalize_origin(str(val_b))
            if o_a.get("normalized_value", {}).get("country") == o_b.get("normalized_value", {}).get("country"):
                return True

        # Substring / overlap match for long strings (e.g. manufacturer, consumer care)
        if len(norm_a) >= 6 and len(norm_b) >= 6:
            if norm_a in norm_b or norm_b in norm_a:
                return True

        return False

    @classmethod
    def reconcile(
        cls,
        tesseract_fields: ExtractedFieldsContainer,
        qwen_fields: ExtractedFieldsContainer
    ) -> Tuple[ExtractedFieldsContainer, Dict[str, ReconciliationDetail]]:
        reconciled_dict: Dict[str, Any] = {}
        reconciliation_ledger: Dict[str, ReconciliationDetail] = {}

        t_dict = tesseract_fields.model_dump()
        q_dict = qwen_fields.model_dump()

        for field_name in REQUIRED_DECLARATION_FIELDS:
            t_res = t_dict.get(field_name) or {}
            q_res = q_dict.get(field_name) or {}

            t_val = t_res.get("value")
            t_conf = float(t_res.get("confidence") or 0.0)
            t_box = t_res.get("bounding_box")
            t_ev = t_res.get("evidence_text") or t_res.get("raw_value")

            q_val = q_res.get("value")
            q_conf = float(q_res.get("confidence") or 0.0)
            q_box = q_res.get("bounding_box")
            q_ev = q_res.get("evidence_text") or q_res.get("raw_value")

            # Filter out erroneous statutory labels when evaluating product_name
            if field_name == "product_name":
                if t_val and STATUTORY_LABEL_REGEX.search(str(t_val)):
                    t_val = None
                    t_conf = 0.0
                if q_val and STATUTORY_LABEL_REGEX.search(str(q_val)):
                    q_val = None
                    q_conf = 0.0

            candidates: List[CandidateObservation] = []
            if t_val:
                candidates.append(CandidateObservation(
                    value=t_val,
                    source="tesseract",
                    confidence=t_conf,
                    evidence_text=t_ev,
                    bounding_box=t_box
                ))
            if q_val:
                candidates.append(CandidateObservation(
                    value=q_val,
                    source="qwen_vision",
                    confidence=q_conf,
                    evidence_text=q_ev,
                    bounding_box=q_box
                ))

            # Case 1: Both detected and agree
            if t_val and q_val and cls._is_equivalent(t_val, q_val, field_name):
                combined_conf = min(0.99, max(t_conf, q_conf) + 0.05)
                reconciled_dict[field_name] = FieldExtractionResult(
                    field=field_name,
                    value=q_val,
                    confidence=combined_conf,
                    source="qwen_vision+tesseract",
                    bounding_box=q_box or t_box,
                    evidence_text=q_ev or t_ev,
                    status="FOUND",
                    raw_value=f"Corroborated: '{q_val}' (Qwen) & '{t_val}' (Tesseract)",
                    conflict_detected=False,
                    candidates=candidates
                )
                reconciliation_ledger[field_name] = ReconciliationDetail(
                    field=field_name,
                    candidates=candidates,
                    resolution="agreement",
                    conflict_detected=False,
                    reconciliation_notes="Tesseract OCR and Qwen Vision corroborated this declaration."
                )

            # Case 2: Both detected but CONFLICT
            elif t_val and q_val and not cls._is_equivalent(t_val, q_val, field_name):
                logger.warning(
                    f"Perception conflict on field '{field_name}': Tesseract='{t_val}' vs Qwen='{q_val}'"
                )
                reconciled_dict[field_name] = FieldExtractionResult(
                    field=field_name,
                    value=q_val,
                    confidence=0.50,
                    source="qwen_vision",
                    bounding_box=q_box or t_box,
                    evidence_text=f"Qwen: '{q_ev}' | Tesseract: '{t_ev}'",
                    status="UNCLEAR",
                    raw_value=f"Conflict: Tesseract='{t_val}', Qwen='{q_val}'",
                    conflict_detected=True,
                    candidates=candidates
                )
                reconciliation_ledger[field_name] = ReconciliationDetail(
                    field=field_name,
                    candidates=candidates,
                    resolution="disagreement",
                    conflict_detected=True,
                    reconciliation_notes=f"Conflicting candidates: Tesseract detected '{t_val}' ({t_conf:.2f}), whereas Qwen Vision detected '{q_val}' ({q_conf:.2f}). Inspector verification required."
                )

            # Case 3: Only Qwen Vision detected (Case A: evaluate normally)
            elif q_val and not t_val:
                reconciled_dict[field_name] = FieldExtractionResult(
                    field=field_name,
                    value=q_val,
                    confidence=max(q_conf, 0.95),
                    source="qwen_vision",
                    bounding_box=q_box,
                    evidence_text=q_ev or q_val,
                    status="FOUND",
                    raw_value=q_val,
                    conflict_detected=False,
                    candidates=candidates
                )
                reconciliation_ledger[field_name] = ReconciliationDetail(
                    field=field_name,
                    candidates=candidates,
                    resolution="single_source",
                    conflict_detected=False,
                    reconciliation_notes="Detected via Qwen Vision primary visual perception."
                )

            # Case 4: Only Tesseract detected (Case B: evaluate normally)
            elif t_val and not q_val:
                reconciled_dict[field_name] = FieldExtractionResult(
                    field=field_name,
                    value=t_val,
                    confidence=max(t_conf, 0.90),
                    source="tesseract",
                    bounding_box=t_box,
                    evidence_text=t_ev or t_val,
                    status="FOUND",
                    raw_value=t_val,
                    conflict_detected=False,
                    candidates=candidates
                )
                reconciliation_ledger[field_name] = ReconciliationDetail(
                    field=field_name,
                    candidates=candidates,
                    resolution="single_source",
                    conflict_detected=False,
                    reconciliation_notes="Detected via Tesseract OCR visual evidence."
                )

            # Case 5: Neither detected
            else:
                reconciled_dict[field_name] = FieldExtractionResult(
                    field=field_name,
                    value=None,
                    confidence=0.0,
                    source="none",
                    bounding_box=None,
                    evidence_text=None,
                    status="NOT_FOUND",
                    raw_value=None,
                    conflict_detected=False,
                    candidates=[]
                )
                reconciliation_ledger[field_name] = ReconciliationDetail(
                    field=field_name,
                    candidates=[],
                    resolution="not_detected",
                    conflict_detected=False,
                    reconciliation_notes="Declaration not detected in scanned panel."
                )

        container = ExtractedFieldsContainer(**reconciled_dict)
        return container, reconciliation_ledger
