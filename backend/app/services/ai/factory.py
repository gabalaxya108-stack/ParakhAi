from backend.app.core.config import settings
from backend.app.services.ai.base import BaseVisionProvider
from backend.app.services.ai.fixture_provider import FixtureVisionProvider

def get_vision_provider() -> BaseVisionProvider:
    provider_name = settings.AI_PROVIDER.lower().strip()
    
    if provider_name in ["azure_openai", "openai"]:
        if settings.OPENAI_API_KEY or (settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY):
            from backend.app.services.ai.openai_provider import OpenAIVisionProvider
            return OpenAIVisionProvider()
    
    elif provider_name == "gemini":
        if settings.GEMINI_API_KEY:
            from backend.app.services.ai.gemini_provider import GeminiVisionProvider
            return GeminiVisionProvider()

    # Default fallback: High-fidelity realistic perception fixture
    return FixtureVisionProvider()
