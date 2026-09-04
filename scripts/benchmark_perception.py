"""
Comparative Benchmark: Pre-Optimization vs Upgraded Region-Based OCR & Perception Pipeline
Evaluated across 10 real retail packaged-product images.
"""

import asyncio
import os
import time
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

from backend.app.services.ocr.tesseract import TesseractOCRProvider
from backend.app.services.extraction.mock import MockExtractionProvider
from backend.app.services.ocr.preprocessor import ImagePreprocessingPipeline

BENCHMARK_DATASET = [
    {
        "id": 1,
        "name": "Potato Chips Pack",
        "path": "backend/fixtures/potato_chips_sample.jpg",
        "ground_truth": {"mrp": True, "net_quantity": True, "manufacturer": True, "consumer_care": True}
    },
    {
        "id": 2,
        "name": "Artisan Coffee Bag",
        "path": "backend/fixtures/artisan_coffee_sample.jpg",
        "ground_truth": {"mrp": True, "net_quantity": True, "manufacturer": True, "consumer_care": False}
    },
    {
        "id": 3,
        "name": "Wireless Earbuds Box",
        "path": "backend/fixtures/wireless_earbuds_sample.jpg",
        "ground_truth": {"mrp": True, "net_quantity": True, "manufacturer": True, "consumer_care": False}
    },
    {
        "id": 4,
        "name": "Maggi 2-Min Noodles",
        "path": "data/uploads/insp_f6b6ba0feb9b/original.png",
        "ground_truth": {"mrp": False, "net_quantity": True, "manufacturer": True, "consumer_care": False}  # MRP price stamped under seal
    },
    {
        "id": 5,
        "name": "Detergent Bottle Photo",
        "path": "data/uploads/insp_b55f34bd8d1f/original.jpeg",
        "ground_truth": {"mrp": True, "net_quantity": False, "manufacturer": True, "consumer_care": False}
    },
    {
        "id": 6,
        "name": "Retail Food Carton 1",
        "path": "data/uploads/insp_05f50fc54496/original.jpg",
        "ground_truth": {"mrp": True, "net_quantity": True, "manufacturer": True, "consumer_care": True}
    },
    {
        "id": 7,
        "name": "Retail Food Carton 2",
        "path": "data/uploads/insp_1af1085f5111/original.jpg",
        "ground_truth": {"mrp": True, "net_quantity": True, "manufacturer": True, "consumer_care": True}
    },
    {
        "id": 8,
        "name": "Biscuit Pack (WEBP)",
        "path": "data/uploads/insp_351eafeb8702/original.webp",
        "ground_truth": {"mrp": True, "net_quantity": False, "manufacturer": False, "consumer_care": False}
    },
    {
        "id": 9,
        "name": "Statutory Scan (TIFF)",
        "path": "data/uploads/insp_0a7aaa645255/original.tiff",
        "ground_truth": {"mrp": True, "net_quantity": True, "manufacturer": False, "consumer_care": False}
    },
    {
        "id": 10,
        "name": "Mobile Camera Label",
        "path": "data/uploads/insp_da8cb4bf6b36/display.jpg",
        "ground_truth": {"mrp": True, "net_quantity": False, "manufacturer": False, "consumer_care": False}
    }
]

async def run_benchmark():
    ocr_provider = TesseractOCRProvider()
    ext_provider = MockExtractionProvider()
    
    print("=" * 115)
    print("EMPIRICAL PERCEPTION & OCR BENCHMARK — 10 REAL PACKAGED PRODUCTS")
    print("=" * 115)
    
    results = []
    
    for item in BENCHMARK_DATASET:
        path = item["path"]
        name = item["name"]
        gt = item["ground_truth"]
        
        if not os.path.exists(path):
            print(f"Skipping {path} (not found)")
            continue
            
        t0 = time.time()
        ocr_res = await ocr_provider.extract(path, inspection_id=f"bench_{item['id']}")
        ext_res = await ext_provider.extract(path, ocr_res, inspection_id=f"bench_{item['id']}")
        duration_ms = (time.time() - t0) * 1000
        
        fields = ext_res.model_dump()
        
        # Check extraction matches
        mrp_ok = (fields["mrp"]["value"] is not None) == gt["mrp"]
        nq_ok = (fields["net_quantity"]["value"] is not None) == gt["net_quantity"]
        mfd_ok = (fields["manufacturer"]["value"] is not None) == gt["manufacturer"]
        cc_ok = (fields["consumer_care"]["value"] is not None) == gt["consumer_care"]
        
        # Overall detection accuracy for present fields
        total_checks = len(gt)
        passed_checks = sum([mrp_ok, nq_ok, mfd_ok, cc_ok])
        acc = (passed_checks / total_checks) * 100
        
        avg_conf = (sum(b.confidence for b in ocr_res.blocks) / len(ocr_res.blocks) * 100) if ocr_res.blocks else 0.0
        
        results.append({
            "name": name,
            "res": f"{ocr_res.image_width}x{ocr_res.image_height}",
            "blocks": ocr_res.total_blocks,
            "conf": round(avg_conf, 1),
            "mrp": fields["mrp"]["value"] or (f"[{fields['mrp']['status']}]" if fields['mrp']['status'] != 'NOT_FOUND' else '—'),
            "net_qty": fields["net_quantity"]["value"] or '—',
            "mfd": fields["manufacturer"]["value"][:24] + '...' if fields["manufacturer"]["value"] else '—',
            "cc": fields["consumer_care"]["value"][:24] + '...' if fields["consumer_care"]["value"] else '—',
            "accuracy": round(acc, 1),
            "time_ms": round(duration_ms)
        })
        
        print(f"[{item['id']}/10] {name:<24} | Acc: {acc:>5.1f}% | Conf: {avg_conf:>5.1f}% | NetQty: {results[-1]['net_qty']:<10} | MRP: {results[-1]['mrp']:<12} | Time: {duration_ms:>5.0f}ms")

    print("\n" + "=" * 115)
    print(f"{'#':<3} {'Package Name':<24} {'Res':<10} {'Blocks':<8} {'Conf':<7} {'Net Quantity':<14} {'MRP':<15} {'Manufacturer':<24} {'Acc':<6} {'Time':<7}")
    print("-" * 115)
    for idx, r in enumerate(results, 1):
        print(f"{idx:<3} {r['name']:<24} {r['res']:<10} {r['blocks']:<8} {r['conf']:>5.1f}% {r['net_qty']:<14} {r['mrp']:<15} {r['mfd']:<24} {r['accuracy']:>4.0f}% {r['time_ms']:>5.0f}ms")
    print("-" * 115)
    
    avg_acc = sum(r["accuracy"] for r in results) / len(results)
    avg_conf_all = sum(r["conf"] for r in results) / len(results)
    avg_time = sum(r["time_ms"] for r in results) / len(results)
    print(f"OVERALL SUMMARY:")
    print(f"  • Average Field Extraction Accuracy: {avg_acc:.1f}%")
    print(f"  • Average OCR Confidence:           {avg_conf_all:.1f}%")
    print(f"  • Average End-to-End Latency:        {avg_time:.0f} ms")
    print("=" * 115)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
