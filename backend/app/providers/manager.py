"""Provider manager: routes inference requests and exposes health/privacy statuses without silent fallback."""

import asyncio
from typing import Dict, List, Optional

from backend.app.config import settings
from backend.app.models.file import FileMetadata
from backend.app.models.plan import FileSuggestion, OrganizationOptions
from backend.app.providers.base import AIProvider, ProviderHealth
from backend.app.providers.gemini_provider import GeminiProvider
from backend.app.providers.mock_provider import MockAIProvider
from backend.app.providers.ollama_provider import OllamaProvider


class ProviderManager:
    """
    Central coordinator for AI providers in SlothSort.

    Invariants:
    1. Zero Silent Fallback: Requests are dispatched ONLY to the explicitly chosen provider.
       If Ollama fails, it does NOT silently call Gemini.
       If Gemini fails, it does NOT silently call Ollama.
    2. Transparent Privacy: Health checks disclose offline vs cloud status.
    3. Separation of Concerns: Provider selection is decoupled from deterministic approval.
    """

    def __init__(
        self,
        providers: Optional[Dict[str, AIProvider]] = None,
        default_provider: Optional[str] = None,
    ):
        if providers is not None:
            self._providers = dict(providers)
        else:
            self._providers = {
                "mock": MockAIProvider(),
                "ollama": OllamaProvider(),
                "gemini": GeminiProvider(),
            }
        self.default_provider_id = default_provider or settings.DEFAULT_PROVIDER

    @property
    def registered_provider_ids(self) -> List[str]:
        return list(self._providers.keys())

    def get_provider(self, provider_id: Optional[str] = None) -> AIProvider:
        """
        Retrieves a provider by ID or returns the default provider.
        Raises ValueError if provider_id is unrecognized.
        """
        target_id = (provider_id or self.default_provider_id).strip().lower()
        if target_id not in self._providers:
            valid_ids = ", ".join(f"'{k}'" for k in self._providers.keys())
            raise ValueError(
                f"Unknown AI provider '{target_id}'. Supported providers are: {valid_ids}."
            )
        return self._providers[target_id]

    async def list_providers_health(self) -> List[ProviderHealth]:
        """
        Checks health and privacy status for all registered providers concurrently.
        """
        provider_list = list(self._providers.values())
        health_results = await asyncio.gather(
            *(p.check_health() for p in provider_list),
            return_exceptions=False,
        )
        return list(health_results)

    async def generate_suggestions(
        self,
        provider_id: Optional[str],
        files: List[FileMetadata],
        options: Optional[OrganizationOptions] = None,
    ) -> List[FileSuggestion]:
        """
        Generates organization suggestions using exclusively the requested provider.

        Strict Non-Fallback Guarantee:
        If the selected provider fails, the error is immediately propagated to the caller.
        The system will NEVER silently re-route to an unapproved provider.
        """
        provider = self.get_provider(provider_id)
        # Directly call provider without fallback catch
        return await provider.generate_suggestions(files, options)
