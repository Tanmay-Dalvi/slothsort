"""AI Providers status and capability API router."""

from typing import List
from fastapi import APIRouter

from backend.app.providers.base import ProviderHealth
from backend.app.providers.manager import ProviderManager

router = APIRouter(tags=["AI Providers"])
_provider_manager = ProviderManager()


@router.get(
    "/providers",
    response_model=List[ProviderHealth],
    summary="List available AI providers",
    description="Reports model name, latency, connection status, and privacy disclosure for all configured AI providers.",
)
async def list_providers() -> List[ProviderHealth]:
    return await _provider_manager.list_providers_health()
