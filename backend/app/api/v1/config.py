from typing import Dict, Any
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.ai.factory import get_vision_provider

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/providers", response_model=Dict[str, Any])
async def get_provider_config():
    """Returns active AI perception provider and available integrations."""
    p = get_vision_provider()
    return {
        "active_provider": type(p).__name__,
        "configured_setting": settings.AI_PROVIDER,
        "supported_providers": [
            {"id": "fixture", "name": "Pre-calibrated Multi-Product Perception Fixture (Instant Offline)", "is_active": type(p).__name__ == "FixtureVisionProvider"},
            {"id": "azure_openai", "name": "Azure OpenAI (GPT-4o Vision)", "is_active": "OpenAI" in type(p).__name__},
            {"id": "gemini", "name": "Google Gemini 1.5/2.0 Flash Vision", "is_active": "Gemini" in type(p).__name__}
        ],
        "available_fixtures": [
            {"id": "potato_chips_sample.jpg", "name": "Desi Crunch Potato Chips (120g) - Non-Compliant ('gms', no USP, no taxes)", "category": "Snack Foods"},
            {"id": "artisan_coffee_sample.jpg", "name": "Artisan Hills Coorg Coffee Beans (250g) - 100% Fully Compliant", "category": "Beverages & Coffee"},
            {"id": "wireless_earbuds_sample.jpg", "name": "SoundWave Pro Bass Wireless Earbuds - Non-Compliant (Missing Origin, Post-dated)", "category": "Electronics"}
        ]
    }
