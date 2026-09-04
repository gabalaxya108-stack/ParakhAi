#!/usr/bin/env python3
"""
Tesseract OCR Benchmark Suite for Legal Metrology Packaged Commodities.
Evaluates local Tesseract 5.5.3 performance, speed, confidence, and packaging keyword extraction.
"""

import os
import sys
import time
import glob
import asyncio
from typing import List, Dict, Any

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.ocr.tesseract import TesseractOCRProvider
from backend.app.core.config import settings

async def run_benchmark(image_paths: List[str], lang: str = "eng+hin"):
    print("=" * 80)
    print("LEGAL METROLOGY TESSERACT OCR BENCHMARK")
    print("=" * 80)

    provider = TesseractOCRProvider()
    version = provider.get_version()
    executable = provider.executable_path
    installed_langs = provider.get_installed_languages()
    resolved_lang = provider.resolve_languages(lang)

    print(f"Provider:                Tesseract OCR (pytesseract)")
    print(f"Executable:              {executable}")
    print(f"Engine Version:          {version}")
    print(f"Installed Languages:     {len(installed_langs)} (Sample: {installed_langs[:8]})")
    print(f"Configured Languages:    {resolved_lang}")
    print(f"Test Images Found:       {len(image_paths)}")
    print("-" * 80)

    if not provider.executable_path:
        print("ERROR: Tesseract binary not found! Check TESSERACT_CMD or PATH.")
        sys.exit(1)

    results: List[Dict[str, Any]] = []
    total_time = 0.0

    print(f"{'#':<3} | {'Image File':<28} | {'Resolution':<12} | {'Time (ms)':<10} | {'Blocks':<8} | {'Avg Conf':<9} | {'Keywords'}")
    print("-" * 80)

    for idx, path in enumerate(image_paths, 1):
        filename = os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path)
        if len(filename) > 28:
            filename = "..." + filename[-25:]

        try:
            res = await provider.extract(path, inspection_id=f"bench_{idx}", lang=resolved_lang)
            duration_ms = res.processing_time_ms
            total_time += duration_ms

            confs = [b.confidence * 100.0 for b in res.blocks]
            avg_conf = (sum(confs) / len(confs)) if confs else 0.0

            # Count statutory keywords
            text_lower = res.full_text.lower()
            keywords_found = []
            for kw in ["mrp", "net", "qty", "mfd", "batch", "pkd", "fssai", "lic", "care"]:
                if kw in text_lower:
                    keywords_found.append(kw)

            kw_str = ",".join(keywords_found) if keywords_found else "none"
            res_str = f"{res.image_width}x{res.image_height}"

            print(f"{idx:<3} | {filename:<28} | {res_str:<12} | {duration_ms:<10.1f} | {res.total_blocks:<8} | {avg_conf:<8.1f}% | {kw_str}")

            results.append({
                "path": path,
                "dims": (res.image_width, res.image_height),
                "duration_ms": duration_ms,
                "blocks": res.total_blocks,
                "avg_conf": avg_conf,
                "keywords": keywords_found,
                "snippet": res.full_text[:80].replace("\n", " ")
            })
        except Exception as e:
            print(f"{idx:<3} | {filename:<28} | ERROR: {str(e)[:35]}")

    print("=" * 80)
    if results:
        valid_confs = [r["avg_conf"] for r in results if r["blocks"] > 0]
        avg_overall_conf = sum(valid_confs) / len(valid_confs) if valid_confs else 0.0
        avg_duration = sum(r["duration_ms"] for r in results) / len(results)
        total_blocks = sum(r["blocks"] for r in results)

        print("BENCHMARK SUMMARY:")
        print(f"Total Images Evaluated:       {len(results)}")
        print(f"Average Processing Duration:  {avg_duration:.1f} ms / image")
        print(f"Total Text Blocks Grounded:   {total_blocks}")
        print(f"Mean Confidence (Active Text): {avg_overall_conf:.1f}%")
        print("=" * 80)

def main():
    if len(sys.argv) > 1:
        selected = sys.argv[1:]
    else:
        # Collect sample images, prioritizing larger real photographs (> 20KB)
        all_images = glob.glob("./data/uploads/*/original.*")
        real_images = [p for p in all_images if os.path.getsize(p) > 20 * 1024]
        selected = (real_images or all_images)[:8]

    if not selected:
        print("No sample images found in ./data/uploads/")
        return

    asyncio.run(run_benchmark(selected, lang=os.getenv("TESSERACT_LANG", "eng+hin")))

if __name__ == "__main__":
    main()
