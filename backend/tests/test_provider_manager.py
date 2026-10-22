"""Tests for ProviderManager: routing, zero silent fallback, and health aggregation."""

from typing import List, Optional
import pytest

from backend.app.models.file import FileMetadata, generate_file_id
from backend.app.models.plan import FileSuggestion, OrganizationOptions
from backend.app.providers.base import AIProvider, ProviderHealth
from backend.app.providers.manager import ProviderManager
from backend.app.providers.mock_provider import MockAIProvider


class FailingLocalProvider(AIProvider):
    """Test double that simulates a crashing or offline local Ollama daemon."""
    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return "gemma3:1b"

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            is_available=False,
            provider_name="Local Ollama",
            model_name=self.default_model,
            error_message="Ollama server connection refused",
            is_cloud=False,
            privacy_notice="100% Local",
        )

    async def generate_suggestions(
        self, files: List[FileMetadata], options: Optional[OrganizationOptions] = None
    ) -> List[FileSuggestion]:
        raise RuntimeError("Local Ollama daemon is offline (ConnectionRefusedError: port 11434)")


class TrackingCloudProvider(AIProvider):
    """Test double that records if it was ever invoked."""
    def __init__(self):
        self.invoked = False

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            is_available=True,
            provider_name="Google Gemini",
            model_name=self.default_model,
            is_cloud=True,
            privacy_notice="Cloud API Active",
        )

    async def generate_suggestions(
        self, files: List[FileMetadata], options: Optional[OrganizationOptions] = None
    ) -> List[FileSuggestion]:
        self.invoked = True
        return []


def test_provider_manager_routing():
    """Verifies that the manager retrieves the requested provider."""
    manager = ProviderManager()
    mock_p = manager.get_provider("mock")
    assert isinstance(mock_p, MockAIProvider)

    with pytest.raises(ValueError, match="Unknown AI provider 'unsupported_model'"):
        manager.get_provider("unsupported_model")


@pytest.mark.asyncio
async def test_zero_silent_cloud_fallback():
    """
    CRITICAL PRIVACY TEST:
    When a user chooses Local Ollama and it fails, the system must NEVER
    silently fall back to cloud AI. It must raise an explicit exception.
    """
    failing_ollama = FailingLocalProvider()
    tracking_gemini = TrackingCloudProvider()

    manager = ProviderManager(
        providers={
            "ollama": failing_ollama,
            "gemini": tracking_gemini,
            "mock": MockAIProvider(),
        }
    )

    test_file = FileMetadata(
        id=generate_file_id("secret_financial_plan.pdf"),
        original_rel_path="secret_financial_plan.pdf",
        filename="secret_financial_plan.pdf",
        extension="pdf",
        size_bytes=1000,
        modified_at="2026-10-22T00:00:00Z",
    )

    # Must raise the Ollama error and NOT call Gemini
    with pytest.raises(RuntimeError, match="Local Ollama daemon is offline"):
        await manager.generate_suggestions("ollama", [test_file])

    # Assert cloud provider was NEVER called
    assert tracking_gemini.invoked is False


@pytest.mark.asyncio
async def test_provider_manager_health_aggregation():
    """Verifies that manager aggregates health statuses across all registered providers."""
    manager = ProviderManager()
    health_list = await manager.list_providers_health()

    assert len(health_list) >= 3
    provider_names = [h.provider_name for h in health_list]
    assert any("Mock" in n for n in provider_names)
    assert any("Ollama" in n for n in provider_names)
    assert any("Gemini" in n for n in provider_names)
