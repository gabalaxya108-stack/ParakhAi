import os
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any, Optional
from backend.app.schemas.common import BoundingBox

class ComputerVisionService:
    @staticmethod
    def preprocess_image(
        input_image_path: str,
        output_image_path: str,
        package_width_cm: Optional[float] = 12.0,
        package_height_cm: Optional[float] = 20.0,
        is_cylindrical: bool = False
    ) -> Dict[str, Any]:
        """
        Reads input image, performs glare reduction (CLAHE), deskewing,
        and calculates PDP dimensions and mm-per-pixel resolution scale.
        """
        img = cv2.imread(input_image_path)
        if img is None:
            # Fallback if image cannot be read directly by OpenCV
            pil_img = Image.open(input_image_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        orig_h, orig_w = img.shape[:2]

        # 1. Glare reduction & Contrast Enhancement using CLAHE on LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 2. Deskew estimation using edge detection & Hough Lines
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        
        deskew_angle = 0.0
        if lines is not None and len(lines) > 0:
            angles = []
            for item in lines:
                pts = item[0] if len(item.shape) > 1 and item.shape[0] == 1 else item
                if len(pts) >= 4:
                    x1, y1, x2, y2 = pts[0], pts[1], pts[2], pts[3]
                    angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                    if abs(angle) < 45.0:
                        angles.append(angle)
            if angles:
                deskew_angle = float(np.median(angles))

        # Rotate if significant deskew needed (> 0.5 degrees and < 30 degrees)
        if abs(deskew_angle) > 0.5 and abs(deskew_angle) < 30.0:
            center = (orig_w // 2, orig_h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, deskew_angle, 1.0)
            enhanced = cv2.warpAffine(
                enhanced, rot_mat, (orig_w, orig_h),
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )

        # Save preprocessed image
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        cv2.imwrite(output_image_path, enhanced)

        # 3. Calculate Principal Display Panel (PDP) Area (Rule 7, PCR 2011)
        w_cm = package_width_cm or 12.0
        h_cm = package_height_cm or 20.0
        
        if is_cylindrical:
            # 40% of circumference * height
            pdp_area_sq_cm = 0.4 * (w_cm * 3.14159) * h_cm
        else:
            # Rectangular face
            pdp_area_sq_cm = w_cm * h_cm

        # Calculate pixel-to-millimeter ratio based on package height
        mm_height = h_cm * 10.0
        mm_per_pixel = mm_height / float(orig_h) if orig_h > 0 else 0.15

        return {
            "width_px": orig_w,
            "height_px": orig_h,
            "deskew_angle_deg": round(deskew_angle, 2),
            "pdp_area_sq_cm": round(pdp_area_sq_cm, 2),
            "mm_per_pixel": round(mm_per_pixel, 4),
            "output_path": output_image_path
        }

    @staticmethod
    def crop_evidence_box(
        image_path: str,
        bbox: BoundingBox,
        output_crop_path: str,
        padding_pct: float = 0.05
    ) -> str:
        """
        Crops an evidence region from an image using normalized bounding box.
        Adds padding and a clean border for presentation in PDF reports.
        """
        img = cv2.imread(image_path)
        if img is None:
            try:
                pil_img = Image.open(image_path).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception:
                return ""

        h, w = img.shape[:2]
        pad_y = (bbox.ymax - bbox.ymin) * padding_pct
        pad_x = (bbox.xmax - bbox.xmin) * padding_pct

        y1 = max(0, int((bbox.ymin - pad_y) * h))
        y2 = min(h, int((bbox.ymax + pad_y) * h))
        x1 = max(0, int((bbox.xmin - pad_x) * w))
        x2 = min(w, int((bbox.xmax + pad_x) * w))

        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            return ""

        # Draw a thin subtle border around evidence
        bordered = cv2.copyMakeBorder(
            crop, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=[30, 144, 255]
        )

        os.makedirs(os.path.dirname(output_crop_path), exist_ok=True)
        cv2.imwrite(output_crop_path, bordered)
        return output_crop_path

    @staticmethod
    def estimate_font_height_mm(bbox: BoundingBox, mm_per_pixel: float, img_height: int) -> float:
        """
        Estimates character height in mm from bounding box pixel height.
        """
        box_px_h = (bbox.ymax - bbox.ymin) * img_height
        # Character height is typically ~65-75% of text block line height
        char_px_h = box_px_h * 0.70
        return round(char_px_h * mm_per_pixel, 2)
