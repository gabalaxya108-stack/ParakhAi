"""
Production-grade Tesseract OCR provider for Indian packaged-commodity label inspection.

Key capabilities:
1. Image Quality Analysis (resolution, blur, brightness, contrast)
2. Quality-driven dynamic upscaling (2x-3x for micro-print)
3. Multi-variant preprocessing (Original, Enhanced, Denoised+Sharpened, Binarized, Morph)
4. Region-based statutory candidate OCR (Header, Statutory Left, Statutory Right, Bottom Panel)
5. Multi-PSM strategy (PSM 3, 6, 11) for full-package, uniform blocks, and sparse labels
6. Spatial & token deduplication preserving highest quality evidence
7. Complete coordinate back-projection to physical package dimensions
8. Forensic preservation of text, confidence, bounding_box, source_variant, and psm_mode
"""

import os
import io
import time
import shutil
import re
from typing import Union, List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import cv2
import numpy as np

from backend.app.services.ocr.base import OCRProvider
from backend.app.services.ocr.preprocessor import ImagePreprocessingPipeline
from backend.app.services.ocr.image_quality import ImageQualityAnalyzer
from backend.app.schemas.ocr import (
    OCRResult,
    OCRBlock,
    PixelBoundingBox,
    NormalizedBoundingBox
)
from backend.app.core.config import settings
from backend.app.core.errors import AppException
from backend.app.core.logging import get_logger

logger = get_logger("services.ocr.tesseract")

# Statutory Legal Metrology packaging declaration keywords for scoring
STATUTORY_KEYWORDS: Set[str] = {
    "mrp", "rs", "₹", "inr", "max", "maximum", "retail", "price", "taxes", "incl",
    "net", "qty", "quantity", "weight", "volume", "mass", "content", "contents",
    "g", "kg", "ml", "l", "ltr", "gm", "gms", "gram", "grams",
    "mfd", "mfg", "manufactured", "manufacturing", "pkd", "packed", "packing",
    "batch", "lot", "bno", "exp", "expiry", "use", "by", "best", "before",
    "consumer", "care", "customer", "feedback", "helpline", "toll", "free",
    "email", "mail", "phone", "tel", "contact", "complaints", "grievance",
    "manufacturer", "marketed", "packer", "importer", "imported",
    "fssai", "lic", "license", "licence", "regd", "registered", "office",
    "unit", "pvt", "ltd", "corp", "limited", "private",
    "origin", "india", "country", "generic", "commodity",
    "ingredients", "nutrition", "allergen", "storage", "serve"
}


class TesseractOCRProvider(OCRProvider):
    """
    Forensic Tesseract OCR provider supporting dynamic upscaling, multi-pass full-image
    and region-based perception for Legal Metrology inspections.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None, default_lang: Optional[str] = None):
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            self.pytesseract = None
            logger.error("pytesseract package is not installed.")

        self.executable_path = self._resolve_executable(tesseract_cmd)
        if self.executable_path and self.pytesseract:
            self.pytesseract.pytesseract.tesseract_cmd = self.executable_path

        self.default_lang = default_lang or os.getenv("TESSERACT_LANG") or getattr(settings, "TESSERACT_LANG", "eng+hin")
        self._cached_version = None
        self._cached_languages = None

    @classmethod
    def _resolve_executable(cls, override_cmd: Optional[str] = None) -> Optional[str]:
        if override_cmd:
            return shutil.which(override_cmd) or (override_cmd if os.path.isfile(override_cmd) and os.access(override_cmd, os.X_OK) else None)

        cmd = os.getenv("TESSERACT_CMD") or getattr(settings, "TESSERACT_CMD", "")
        if cmd:
            resolved = shutil.which(cmd) or (cmd if os.path.isfile(cmd) and os.access(cmd, os.X_OK) else None)
            if resolved:
                return resolved

        resolved = shutil.which("tesseract")
        if resolved:
            return resolved

        for loc in [
            "/opt/homebrew/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/usr/bin/tesseract",
            "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]:
            if os.path.isfile(loc) and os.access(loc, os.X_OK):
                return loc

        return None

    def get_version(self) -> str:
        if self._cached_version:
            return self._cached_version
        if not self.executable_path or not self.pytesseract:
            return "unknown"
        try:
            v = str(self.pytesseract.get_tesseract_version()).strip()
            self._cached_version = v
            return v
        except Exception as e:
            logger.warning(f"Unable to query Tesseract version: {e}")
            return "unknown"

    def get_installed_languages(self) -> List[str]:
        if self._cached_languages:
            return self._cached_languages
        if not self.executable_path or not self.pytesseract:
            return []
        try:
            langs = list(self.pytesseract.get_languages())
            self._cached_languages = langs
            return langs
        except Exception as e:
            logger.warning(f"Unable to query Tesseract installed languages: {e}")
            return []

    def resolve_languages(self, requested_lang: Optional[str] = None) -> str:
        target = requested_lang or self.default_lang
        installed = set(self.get_installed_languages())
        if not installed:
            return target or "eng"

        parts = [p.strip() for p in target.split("+") if p.strip()]
        valid_parts = [p for p in parts if p in installed]

        if valid_parts:
            return "+".join(valid_parts)
        if "eng" in installed:
            return "eng"
        return next(iter(installed))

    def _run_pass(
        self,
        img_arr: np.ndarray,
        lang: str,
        psm: int,
        custom_config: str = ""
    ) -> Optional[Dict[str, Any]]:
        config = f"--psm {psm} --oem 3"
        if custom_config:
            config += f" {custom_config}"

        try:
            return self.pytesseract.image_to_data(
                img_arr,
                lang=lang,
                config=config,
                output_type=self.pytesseract.Output.DICT
            )
        except Exception as e:
            logger.debug(f"Tesseract pass failed (PSM {psm}): {e}")
            return None

    def _parse_data_to_blocks(
        self,
        data: Dict[str, Any],
        scale: float,
        orig_w: int,
        orig_h: int,
        offset_x: int = 0,
        offset_y: int = 0,
        source_variant: str = "original",
        psm_mode: int = 3,
        region: str = "full"
    ) -> Tuple[List[OCRBlock], List[str], float]:
        n_entries = len(data.get("text", []))
        lines_map = defaultdict(list)

        for i in range(n_entries):
            raw_text = data["text"][i].strip()
            conf_raw = float(data["conf"][i])
            if raw_text and conf_raw >= 0:
                line_key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                lines_map[line_key].append(i)

        blocks: List[OCRBlock] = []
        all_words: List[str] = []

        for line_key, idxs in lines_map.items():
            line_words = [data["text"][idx].strip() for idx in idxs]
            line_text = " ".join(line_words)
            all_words.extend(line_words)

            raw_left = min(data["left"][idx] for idx in idxs) + offset_x
            raw_top = min(data["top"][idx] for idx in idxs) + offset_y
            raw_right = max(data["left"][idx] + data["width"][idx] for idx in idxs) + offset_x
            raw_bottom = max(data["top"][idx] + data["height"][idx] for idx in idxs) + offset_y
            avg_line_conf = round((sum(float(data["conf"][idx]) for idx in idxs) / len(idxs)) / 100.0, 2)

            x = max(0, int(float(raw_left) / scale))
            y = max(0, int(float(raw_top) / scale))
            w = max(1, min(orig_w - x, int(float(raw_right - raw_left) / scale)))
            h = max(1, min(orig_h - y, int(float(raw_bottom - raw_top) / scale)))

            ymin = max(0.0, min(1.0, y / float(orig_h)))
            xmin = max(0.0, min(1.0, x / float(orig_w)))
            ymax = max(0.0, min(1.0, (y + h) / float(orig_h)))
            xmax = max(0.0, min(1.0, (x + w) / float(orig_w)))

            line_block = OCRBlock(
                text=line_text,
                confidence=avg_line_conf,
                bounding_box=PixelBoundingBox(x=x, y=y, width=w, height=h),
                normalized_box=NormalizedBoundingBox(ymin=ymin, xmin=xmin, ymax=ymax, xmax=xmax),
                page_number=1,
                source_image_variant=source_variant,
                psm_mode=psm_mode,
                region=region
            )
            blocks.append(line_block)

            # Granular word blocks for precision evidence grounding
            if len(idxs) > 1:
                for idx in idxs:
                    w_text = data["text"][idx].strip()
                    w_conf = round(float(data["conf"][idx]) / 100.0, 2)
                    wx = max(0, int(float(data["left"][idx] + offset_x) / scale))
                    wy = max(0, int(float(data["top"][idx] + offset_y) / scale))
                    ww = max(1, min(orig_w - wx, int(float(data["width"][idx]) / scale)))
                    wh = max(1, min(orig_h - wy, int(float(data["height"][idx]) / scale)))

                    word_block = OCRBlock(
                        text=w_text,
                        confidence=w_conf,
                        bounding_box=PixelBoundingBox(x=wx, y=wy, width=ww, height=wh),
                        normalized_box=NormalizedBoundingBox(
                            ymin=max(0.0, min(1.0, wy / float(orig_h))),
                            xmin=max(0.0, min(1.0, wx / float(orig_w))),
                            ymax=max(0.0, min(1.0, (wy + wh) / float(orig_h))),
                            xmax=max(0.0, min(1.0, (wx + ww) / float(orig_w)))
                        ),
                        page_number=1,
                        source_image_variant=source_variant,
                        psm_mode=psm_mode,
                        region=region
                    )
                    blocks.append(word_block)

        confs = [b.confidence * 100.0 for b in blocks if " " in b.text or len(blocks) < 5]
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        return blocks, all_words, avg_conf

    @staticmethod
    def _compute_iou(b1: PixelBoundingBox, b2: PixelBoundingBox) -> float:
        x_left = max(b1.x, b2.x)
        y_top = max(b1.y, b2.y)
        x_right = min(b1.x + b1.width, b2.x + b2.width)
        y_bottom = min(b1.y + b1.height, b2.y + b2.height)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        b1_area = b1.width * b1.height
        b2_area = b2.width * b2.height
        union_area = float(b1_area + b2_area - intersection_area)

        if union_area <= 0:
            return 0.0
        return intersection_area / union_area

    def _deduplicate_blocks(self, raw_blocks: List[OCRBlock]) -> List[OCRBlock]:
        """
        Deduplicates overlapping blocks across multiple passes and regional crops.
        Prefers blocks with higher confidence, more complete text, or statutory keywords.
        """
        # Separate line blocks and word blocks
        line_blocks = [b for b in raw_blocks if " " in b.text]
        word_blocks = [b for b in raw_blocks if " " not in b.text]

        # Deduplicate line blocks
        deduped_lines: List[OCRBlock] = []
        for candidate in sorted(line_blocks, key=lambda b: (-b.confidence, -len(b.text))):
            overlapping = False
            for existing in deduped_lines:
                iou = self._compute_iou(candidate.bounding_box, existing.bounding_box)
                # If high spatial overlap (> 0.55) or identical text in near coordinates
                if iou > 0.55 or (candidate.text.lower() == existing.text.lower() and iou > 0.25):
                    overlapping = True
                    break
            if not overlapping:
                deduped_lines.append(candidate)

        # Retain non-colliding word blocks for fine evidence grounding
        deduped_words: List[OCRBlock] = []
        for wb in word_blocks:
            # Only keep word block if it contains meaningful tokens
            if len(wb.text) >= 2:
                deduped_words.append(wb)

        consolidated = deduped_lines + deduped_words
        consolidated.sort(key=lambda b: (b.bounding_box.y // 15, b.bounding_box.x))
        return consolidated

    async def extract(
        self,
        image_input: Union[str, bytes],
        inspection_id: str = "",
        lang: Optional[str] = None
    ) -> OCRResult:
        if not self.executable_path or not self.pytesseract:
            raise AppException(
                message="Tesseract OCR executable not found on host machine. Verify TESSERACT_CMD or system PATH.",
                error_code="TESSERACT_NOT_FOUND",
                status_code=503
            )

        start_time = time.time()
        active_lang = self.resolve_languages(lang)
        version = self.get_version()

        # 1. Generate full-image preprocessing variants
        try:
            variants = ImagePreprocessingPipeline.generate_variants(image_input)
            rois = ImagePreprocessingPipeline.extract_statutory_rois(image_input)
        except Exception as e:
            logger.error(f"Failed to preprocess image for OCR: {e}")
            raise AppException(
                message="Package image could not be processed. Please upload a valid, uncorrupted image.",
                error_code="INVALID_IMAGE",
                status_code=400
            )

        first_var = next(iter(variants.values()))
        orig_w, orig_h = first_var["original_dims"]
        quality_metrics = first_var.get("quality_report", {})

        all_candidate_blocks: List[OCRBlock] = []

        # 2. Run Full-Image Passes
        # Pass 1: Original upscaled (PSM 3)
        if "original" in variants:
            data = self._run_pass(variants["original"]["image"], active_lang, psm=3)
            if data:
                b, _, _ = self._parse_data_to_blocks(
                    data, variants["original"]["scale_factor"], orig_w, orig_h,
                    source_variant="original_upscaled", psm_mode=3, region="full"
                )
                all_candidate_blocks.extend(b)

        # Pass 2: Enhanced CLAHE (PSM 3)
        if "enhanced" in variants:
            data = self._run_pass(variants["enhanced"]["image"], active_lang, psm=3)
            if data:
                b, _, _ = self._parse_data_to_blocks(
                    data, variants["enhanced"]["scale_factor"], orig_w, orig_h,
                    source_variant="enhanced_clahe", psm_mode=3, region="full"
                )
                all_candidate_blocks.extend(b)

        # Pass 3: Morphological cleanup (PSM 3)
        if "morph" in variants:
            data = self._run_pass(variants["morph"]["image"], active_lang, psm=3)
            if data:
                b, _, _ = self._parse_data_to_blocks(
                    data, variants["morph"]["scale_factor"], orig_w, orig_h,
                    source_variant="morph_clean", psm_mode=3, region="full"
                )
                all_candidate_blocks.extend(b)

        # 3. Run Targeted Region-Based OCR (Crucial for small print / declarations)
        for roi in rois:
            roi_name = roi["name"]
            roi_img = roi["image"]
            scale = roi["scale_factor"]
            crop_x, crop_y, _, _ = roi["crop_rect"]
            psm = roi.get("preferred_psm", 6)

            data = self._run_pass(roi_img, active_lang, psm=psm)
            if data:
                b, _, _ = self._parse_data_to_blocks(
                    data, scale, orig_w, orig_h,
                    offset_x=crop_x, offset_y=crop_y,
                    source_variant=f"roi_{roi_name}", psm_mode=psm, region=roi_name
                )
                all_candidate_blocks.extend(b)

        # 4. Spatial & Token Deduplication
        final_blocks = self._deduplicate_blocks(all_candidate_blocks)

        full_text = " ".join(b.text for b in final_blocks if " " in b.text or len(final_blocks) < 5)
        if not full_text:
            full_text = " ".join(b.text for b in final_blocks)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        results_list = [
            {
                "text": b.text,
                "confidence": round(b.confidence * 100.0, 1),
                "bounding_box": {
                    "x": b.bounding_box.x,
                    "y": b.bounding_box.y,
                    "width": b.bounding_box.width,
                    "height": b.bounding_box.height
                },
                "source_image_variant": b.source_image_variant,
                "psm_mode": b.psm_mode,
                "region": b.region
            }
            for b in final_blocks
        ]

        logger.info(
            f"Tesseract OCR extracted {len(final_blocks)} consolidated blocks in {duration_ms:.0f}ms "
            f"(candidates: {len(all_candidate_blocks)}, regions: {len(rois)}, upscaled: {quality_metrics.get('recommended_upscale', 1.0)}x)"
        )

        return OCRResult(
            inspection_id=inspection_id,
            full_text=full_text,
            blocks=final_blocks,
            total_blocks=len(final_blocks),
            image_width=orig_w,
            image_height=orig_h,
            provider="tesseract",
            version=version,
            languages=active_lang.split("+"),
            processing_time_ms=duration_ms,
            results=results_list,
            quality_metrics=quality_metrics
        )
