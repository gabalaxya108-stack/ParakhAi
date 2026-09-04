import time
import io
from typing import Union, List, Dict, Any
from PIL import Image
from backend.app.services.ocr.base import OCRProvider
from backend.app.schemas.ocr import OCRResult, OCRBlock, PixelBoundingBox, NormalizedBoundingBox

class MockOCRProvider(OCRProvider):
    """
    Deterministic Mock OCR Provider for CI/CD and offline verification.
    """

    async def extract(
        self,
        image_input: Union[str, bytes],
        inspection_id: str = "",
        lang: str = "eng"
    ) -> OCRResult:
        start_time = time.time()

        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = Image.open(image_input)

        img_w, img_h = img.size

        mock_boxes = [
            {"text": "POTATO CHIPS", "conf": 0.98, "x": 100, "y": 150, "w": 300, "h": 50},
            {"text": "NET QUANTITY: 100 g", "conf": 0.96, "x": 100, "y": 250, "w": 250, "h": 40},
            {"text": "MRP Rs 40.00 (INCL. OF ALL TAXES)", "conf": 0.95, "x": 100, "y": 320, "w": 400, "h": 40},
            {"text": "Mfd by: Snack Foods Pvt Ltd, Industrial Area, Solan, HP - 173212", "conf": 0.94, "x": 100, "y": 400, "w": 550, "h": 60},
            {"text": "For feedback/complaints contact Consumer Care Officer: 1800-111-222, email: care@snackfoods.com", "conf": 0.92, "x": 100, "y": 500, "w": 600, "h": 60},
            {"text": "Batch No: SF-2026-X1", "conf": 0.97, "x": 100, "y": 600, "w": 200, "h": 35},
            {"text": "Pkd: 01/2026", "conf": 0.95, "x": 350, "y": 600, "w": 150, "h": 35},
            {"text": "Best Before 6 Months from Packaging", "conf": 0.93, "x": 100, "y": 650, "w": 320, "h": 35},
            {"text": "Country of Origin: India", "conf": 0.99, "x": 100, "y": 720, "w": 220, "h": 35},
            {"text": "Generic Name: Potato Wafers", "conf": 0.91, "x": 100, "y": 770, "w": 260, "h": 35},
            {"text": "Unit Sale Price: Rs 0.40 / g", "conf": 0.94, "x": 100, "y": 820, "w": 240, "h": 35},
        ]

        blocks: List[OCRBlock] = []
        full_text_lines: List[str] = []

        for item in mock_boxes:
            x, y, w, h = item["x"], item["y"], item["w"], item["h"]
            ymin = max(0.0, min(1.0, y / float(img_h)))
            xmin = max(0.0, min(1.0, x / float(img_w)))
            ymax = max(0.0, min(1.0, (y + h) / float(img_h)))
            xmax = max(0.0, min(1.0, (x + w) / float(img_w)))

            block = OCRBlock(
                text=item["text"],
                confidence=item["conf"],
                bounding_box=PixelBoundingBox(x=x, y=y, width=w, height=h),
                normalized_box=NormalizedBoundingBox(ymin=ymin, xmin=xmin, ymax=ymax, xmax=xmax),
                page_number=1
            )
            blocks.append(block)
            full_text_lines.append(item["text"])

        processing_time = round((time.time() - start_time) * 1000, 2)

        results_list = [
            {
                "text": b.text,
                "confidence": round(b.confidence * 100.0, 1),
                "bounding_box": {
                    "x": b.bounding_box.x,
                    "y": b.bounding_box.y,
                    "width": b.bounding_box.width,
                    "height": b.bounding_box.height
                }
            }
            for b in blocks
        ]

        return OCRResult(
            inspection_id=inspection_id,
            full_text=" ".join(full_text_lines),
            blocks=blocks,
            total_blocks=len(blocks),
            image_width=img_w,
            image_height=img_h,
            provider="mock",
            version="mock",
            languages=["eng"],
            processing_time_ms=processing_time,
            results=results_list
        )
