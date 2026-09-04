import os
"""
Advanced forensic image preprocessing pipeline for Indian packaged commodities.

Features:
- Image quality analysis (blur, brightness, contrast, resolution)
- Adaptive quality-driven upscaling (2x - 3x for micro-print)
- Multi-variant generation (Original, Enhanced, Denoised+Sharpened, Adaptive, Morph)
- Region-based statutory candidate extraction (Header, Statutory Left, Statutory Right, Bottom Panel)
"""

import io
import cv2
import numpy as np
from PIL import Image, ImageOps
from typing import Dict, Tuple, Union, List, Optional, Any
from backend.app.services.ocr.image_quality import ImageQualityAnalyzer
from backend.app.core.logging import get_logger

logger = get_logger("services.ocr.preprocessor")


class ImagePreprocessingPipeline:
    """
    Forensic image preprocessing pipeline for Legal Metrology packaging inspections.
    Preserves original image dimensions for forensic back-projection while generating
    targeted full-image and regional variants for Tesseract OCR.
    """

    @classmethod
    def load_and_orient(cls, image_input: Union[str, bytes]) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Loads the image, applies EXIF orientation normalization, and converts to BGR numpy array.
        Returns (bgr_image, (original_width, original_height)).
        """
        if isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input))
        else:
            pil_img = Image.open(image_input)

        try:
            pil_img = ImageOps.exif_transpose(pil_img)
        except Exception as e:
            logger.debug(f"EXIF orientation transpose skipped: {e}")

        if pil_img.mode not in ("RGB", "L"):
            pil_img = pil_img.convert("RGB")

        orig_w, orig_h = pil_img.size

        if pil_img.mode == "L":
            gray_arr = np.array(pil_img)
            bgr_img = cv2.cvtColor(gray_arr, cv2.COLOR_GRAY2BGR)
        else:
            rgb_arr = np.array(pil_img)
            bgr_img = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

        return bgr_img, (orig_w, orig_h)

    @classmethod
    def deskew_image(cls, gray_img: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Calculates dominant text skew angle using minAreaRect on contours
        and corrects skew via affine rotation.
        """
        try:
            thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 100:
                return gray_img, 0.0

            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            if abs(angle) < 0.5 or abs(angle) > 30.0:
                return gray_img, 0.0

            (h, w) = gray_img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(gray_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated, angle
        except Exception as e:
            logger.debug(f"Deskewing skipped: {e}")
            return gray_img, 0.0

    @classmethod
    def upscale_image(cls, bgr_img: np.ndarray, quality_report: Dict[str, Any]) -> Tuple[np.ndarray, float]:
        """
        Dynamically upscales small package images based on quality analysis.
        Target: ~2x-3x for low-res packaging to make micro-text readable by Tesseract.
        """
        scale_factor = quality_report.get("recommended_upscale", 1.0)
        h, w = bgr_img.shape[:2]

        if scale_factor > 1.05:
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            upscaled = cv2.resize(bgr_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            return upscaled, scale_factor

        return bgr_img.copy(), 1.0

    @classmethod
    def make_enhanced_gray(cls, gray: np.ndarray) -> np.ndarray:
        """Grayscale + Bilateral Denoising + CLAHE contrast boost."""
        denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
        return clahe.apply(denoised)

    @classmethod
    def make_denoised_sharpened(cls, gray: np.ndarray) -> np.ndarray:
        """Denoised + Unsharp Mask edge sharpening (boosts micro-print edges)."""
        denoised = cv2.medianBlur(gray, 3)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)
        blurred = cv2.GaussianBlur(contrast, (0, 0), sigmaX=3)
        sharpened = cv2.addWeighted(contrast, 1.6, blurred, -0.6, 0)
        return sharpened

    @classmethod
    def make_adaptive_binary(cls, gray: np.ndarray, block_size: int = 21, c_val: int = 8) -> np.ndarray:
        """Adaptive Gaussian thresholding for variable packaging illumination."""
        denoised = cv2.medianBlur(gray, 3)
        return cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=block_size, C=c_val
        )

    @classmethod
    def make_morph_clean(cls, gray: np.ndarray) -> np.ndarray:
        """Morphological closing + opening to reconnect dot-matrix printed characters."""
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        return cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

    @classmethod
    def generate_variants(
        cls,
        image_input: Union[str, bytes]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generates full-image preprocessing variants driven by image quality analysis:
        1. 'original': Upscaled RGB image
        2. 'enhanced': CLAHE contrast boost
        3. 'denoised_sharpened': Bilateral + unsharp mask
        4. 'binarized': Otsu global threshold
        5. 'adaptive': Adaptive Gaussian threshold
        6. 'morph': Morphological closing
        """
        bgr_img, (orig_w, orig_h) = cls.load_and_orient(image_input)

        # 1. Quality Analysis
        quality_report = ImageQualityAnalyzer.analyze(bgr_img)

        # 2. Upscale
        bgr_scaled, scale_factor = cls.upscale_image(bgr_img, quality_report)

        # 3. Grayscale
        gray = cv2.cvtColor(bgr_scaled, cv2.COLOR_BGR2GRAY)

        # 4. Deskew
        deskewed, skew_angle = cls.deskew_image(gray)

        common_meta = {
            "scale_factor": scale_factor,
            "original_dims": (orig_w, orig_h),
            "quality_report": quality_report,
            "skew_angle": skew_angle
        }

        # Otsu binary
        _, otsu_bin = cv2.threshold(deskewed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return {
            "original": {
                "image": bgr_scaled,
                "is_binary": False,
                **common_meta
            },
            "enhanced": {
                "image": cls.make_enhanced_gray(deskewed),
                "is_binary": False,
                **common_meta
            },
            "denoised_sharpened": {
                "image": cls.make_denoised_sharpened(deskewed),
                "is_binary": False,
                **common_meta
            },
            "binarized": {
                "image": otsu_bin,
                "is_binary": True,
                **common_meta
            },
            "adaptive": {
                "image": cls.make_adaptive_binary(deskewed),
                "is_binary": True,
                **common_meta
            },
            "morph": {
                "image": cls.make_morph_clean(deskewed),
                "is_binary": True,
                **common_meta
            }
        }

    @classmethod
    def extract_statutory_rois(
        cls,
        image_input: Union[str, bytes]
    ) -> List[Dict[str, Any]]:
        """
        Generates targeted statutory candidate regions of interest (ROIs):
        - 'header': Product branding & commodity identity (top 35%)
        - 'statutory_left': Manufacturer, Packer, FSSAI, Batch, Date panel (middle-lower left)
        - 'statutory_right': Nutrition, Ingredients, Consumer Care (middle-lower right)
        - 'bottom_panel': Net quantity, MRP, Barcode, FSSAI (bottom 35%)

        Each ROI includes crop image and offset (crop_x, crop_y) for coordinate back-projection.
        """
        bgr_img, (orig_w, orig_h) = cls.load_and_orient(image_input)
        quality_report = ImageQualityAnalyzer.analyze(bgr_img)
        bgr_scaled, scale_factor = cls.upscale_image(bgr_img, quality_report)
        sh, sw = bgr_scaled.shape[:2]

        roi_definitions = [
            ("header", 0.0, 0.0, 1.0, 0.38, 3),             # Full width, top 38%
            ("statutory_left", 0.0, 0.32, 0.65, 0.68, 6),    # Left column, middle-lower
            ("statutory_right", 0.40, 0.32, 0.60, 0.68, 6),   # Right column, middle-lower
            ("bottom_panel", 0.0, 0.65, 1.0, 0.35, 6),       # Full width, bottom 35%
        ]

        rois = []
        for name, rx_pct, ry_pct, rw_pct, rh_pct, preferred_psm in roi_definitions:
            x1 = max(0, int(sw * rx_pct))
            y1 = max(0, int(sh * ry_pct))
            x2 = min(sw, int(sw * (rx_pct + rw_pct)))
            y2 = min(sh, int(sh * (ry_pct + rh_pct)))

            if (x2 - x1) < 40 or (y2 - y1) < 30:
                continue

            crop = bgr_scaled[y1:y2, x1:x2]
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            enhanced_crop = cls.make_enhanced_gray(gray_crop)

            rois.append({
                "name": name,
                "image": enhanced_crop,
                "crop_rect": (x1, y1, x2 - x1, y2 - y1),  # in upscaled space
                "scale_factor": scale_factor,
                "original_dims": (orig_w, orig_h),
                "preferred_psm": preferred_psm
            })

        return rois

    @classmethod
    def prepare_and_persist_processed_image(
        cls,
        original_image_path: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Processes image for Vision AI and Tesseract OCR while strictly preserving the original.
        Generates a high-fidelity processed image with:
        - EXIF orientation correction
        - Dynamic resolution upscaling
        - LAB-space CLAHE contrast enhancement
        - Unsharp mask edge sharpening
        - Deskewing where applicable
        
        Saves as processed.jpg alongside the original image.
        Returns: (processed_image_path, preprocessing_status, metadata)
        """
        if not os.path.exists(original_image_path):
            return original_image_path, "fallback_original", {"error": "Original image not found"}

        dir_name = os.path.dirname(original_image_path)
        processed_path = os.path.join(dir_name, "processed.jpg")

        try:
            # 1. Load and orient
            bgr_img, (orig_w, orig_h) = cls.load_and_orient(original_image_path)
            
            # 2. Quality analysis
            quality_report = ImageQualityAnalyzer.analyze(bgr_img)
            
            # 3. Dynamic upscale if useful
            bgr_scaled, scale_factor = cls.upscale_image(bgr_img, quality_report)
            
            # 4. Contrast enhancement in LAB color space to preserve color while boosting text contrast
            lab = cv2.cvtColor(bgr_scaled, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l_channel)
            lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
            bgr_contrast = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            
            # 5. Unsharp mask sharpening for micro-text edges
            blurred = cv2.GaussianBlur(bgr_contrast, (0, 0), sigmaX=3.0)
            sharpened = cv2.addWeighted(bgr_contrast, 1.4, blurred, -0.4, 0)
            
            # 6. Save processed image without touching original
            cv2.imwrite(processed_path, sharpened, [cv2.IMWRITE_JPEG_QUALITY, 92])
            
            meta = {
                "original_dimensions": {"width": orig_w, "height": orig_h},
                "processed_dimensions": {"width": sharpened.shape[1], "height": sharpened.shape[0]},
                "scale_factor": scale_factor,
                "quality_metrics": {
                    "is_low_res": quality_report.get("is_low_res", False),
                    "is_blurry": quality_report.get("is_blurry", False),
                    "sharpness": quality_report.get("sharpness", 0.0),
                    "contrast": quality_report.get("contrast", 0.0)
                }
            }
            return processed_path, "processed", meta
        except Exception as e:
            logger.warning(f"Image preprocessing failed, falling back to original: {e}")
            return original_image_path, "fallback_original", {"error": str(e)}

PackageImagePreprocessor = ImagePreprocessingPipeline
