import os
import shutil
from backend.app.core.config import settings
from backend.app.db.repository import InspectionRepository
from backend.app.schemas.inspection import InspectionCreateRequest
from backend.app.services.ai.fixture_provider import FixtureVisionProvider
from backend.app.services.rule_engine.engine import LegalMetrologyRuleEngine
from backend.app.services.cv_service import ComputerVisionService
import asyncio

async def seed_data():
    InspectionRepository.initialize_db()

    # Check if inspections already exist
    existing = InspectionRepository.list_inspections()
    if len(existing) >= 3:
        print("Database already seeded with inspections.")
        return

    provider = FixtureVisionProvider()

    # Copy sample fixture images to uploads
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    samples = [
        {
            "name": "Crunchy Magic Masala Potato Chips (120g)",
            "brand": "Desi Crunch",
            "category": "Snack Foods",
            "batch": "LOT-2026-B88",
            "fixture_img": "potato_chips_sample.jpg",
            "pdp_w": 15.0, "pdp_h": 22.0
        },
        {
            "name": "Artisan Hills Coorg Coffee Beans (250g)",
            "brand": "Artisan Hills",
            "category": "Beverages & Coffee",
            "batch": "BATCH-AH-904",
            "fixture_img": "artisan_coffee_sample.jpg",
            "pdp_w": 14.0, "pdp_h": 24.0
        },
        {
            "name": "SoundWave Pro Bass Wireless Earbuds (Imported)",
            "brand": "SoundWave",
            "category": "Electronics",
            "batch": "SW-EB-2026",
            "fixture_img": "wireless_earbuds_sample.jpg",
            "pdp_w": 12.0, "pdp_h": 16.0
        }
    ]

    for item in samples:
        src = os.path.join(settings.FIXTURES_DIR, item["fixture_img"])
        dest = os.path.join(settings.UPLOAD_DIR, item["fixture_img"])
        if os.path.exists(src) and not os.path.exists(dest):
            shutil.copyfile(src, dest)

        cv_res = ComputerVisionService.preprocess_image(
            input_image_path=dest,
            output_image_path=os.path.join(settings.UPLOAD_DIR, f"prep_{item['fixture_img']}"),
            package_width_cm=item["pdp_w"],
            package_height_cm=item["pdp_h"]
        )

        extraction = await provider.extract_declarations(
            image_path=dest,
            commodity_category=item["category"],
            pdp_area_sq_cm=cv_res["pdp_area_sq_cm"],
            mm_per_pixel=cv_res["mm_per_pixel"]
        )

        scorecard = LegalMetrologyRuleEngine.evaluate(
            declarations=extraction.declarations,
            pdp_area_sq_cm=cv_res["pdp_area_sq_cm"],
            commodity_category=item["category"]
        )

        req = InspectionCreateRequest(
            commodity_name=item["name"],
            commodity_category=item["category"],
            brand_name=item["brand"],
            batch_number=item["batch"],
            package_width_cm=item["pdp_w"],
            package_height_cm=item["pdp_h"]
        )

        resp = InspectionRepository.create_inspection(
            req=req,
            image_url=f"/uploads/{item['fixture_img']}",
            preprocessed_image_url=f"/uploads/prep_{item['fixture_img']}",
            pdp_area_sq_cm=cv_res["pdp_area_sq_cm"],
            declarations=extraction.declarations,
            scorecard=scorecard
        )
        print(f"Seeded: {resp.commodity_name} -> {resp.inspection_number} ({resp.overall_compliance.value})")

if __name__ == "__main__":
    asyncio.run(seed_data())
