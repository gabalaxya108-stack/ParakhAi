import cv2
import numpy as np
from typing import Dict, Any, Tuple
from backend.app.core.logging import get_logger

logger = get_logger("services.ocr.image_quality")

class ImageQualityAnalyzer:
    """
    Forensic image quality analyzer for retail package commodity images.
    Inspects resolution, blur, brightness, contrast, and determines optimal upscale factors.
    """

    @classmethod
    def analyze(cls, bgr_image: np.ndarray) -> Dict[str, Any]:
        h, w = bgr_image.shape[:2]
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY) if len(bgr_image.shape) == 3 else bgr_image

        # 1. Blur evaluation via Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_var = float(laplacian.var())
        is_blurry = blur_var < 85.0

        # 2. Brightness evaluation (mean grayscale intensity)
        brightness_mean = float(np.mean(gray))
        is_dark = brightness_mean < 55.0
        is_overexposed = brightness_mean > 215.0

        # 3. Contrast evaluation (standard deviation of pixel intensities)
        contrast_std = float(np.std(gray))
        is_low_contrast = contrast_std < 38.0

        # 4. Determine upscale factor for micro-text readability
        # Small packaging print requires ~30-50px font height for Tesseract LSTM
        min_dim = min(w, h)
        if min_dim < 750:
            upscale_factor = 3.0
        elif min_dim < 1300:
            upscale_factor = 2.0
        elif min_dim < 2000:
            upscale_factor = 1.5
        else:
            upscale_factor = 1.0

        target_w = int(w * upscale_factor)
        target_h = int(h * upscale_factor)

        # Cap max dimensions at 4200 to maintain fast execution
        if max(target_w, target_h) > 4200:
            scale_down = 4200.0 / float(max(target_w, target_h))
            upscale_factor *= scale_down
            target_w = int(w * upscale_factor)
            target_h = int(h * upscale_factor)

        quality_report = {
            "original_width": w,
            "original_height": h,
            "megapixels": round((w * h) / 1_000_000.0, 2),
            "blur_variance": round(blur_var, 1),
            "is_blurry": is_blurry,
            "brightness_mean": round(brightness_mean, 1),
            "is_dark": is_dark,
            "is_overexposed": is_overexposed,
            "contrast_std": round(contrast_std, 1),
            "is_low_contrast": is_low_contrast,
            "recommended_upscale": round(upscale_factor, 2),
            "target_resolution": (target_w, target_h)
        }

        logger.debug(f"Image Quality Analysis: {w}x{h} -> scale={upscale_factor:.2f}, blur={blur_var:.1f}, contrast={contrast_std:.1f}")
        return quality_report
