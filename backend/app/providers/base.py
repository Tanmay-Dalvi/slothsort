"""Abstract base classes and schemas for AI providers."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.models.file import FileMetadata
from backend.app.models.plan import FileSuggestion, OrganizationOptions


class ProviderHealth(BaseModel):
    """Health status and capability metadata for an AI provider."""
    is_available: bool = Field(description="Whether the provider endpoint/model is reachable")
    provider_name: str = Field(description="Display name of the provider")
    model_name: str = Field(description="Underlying model identifier")
    latency_ms: float = Field(default=0.0, ge=0, description="Ping / generation roundtrip latency")
    error_message: Optional[str] = Field(default=None, description="Diagnostic error if unavailable")
    is_cloud: bool = Field(default=False, description="True if inference calls an external cloud API")
    privacy_notice: str = Field(description="User-facing disclosure of data handling")


class AIProvider(ABC):
    """Base interface for all SlothSort AI providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Machine identifier (e.g. 'mock', 'ollama', 'gemini')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model name."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Verify provider availability and measure baseline latency."""
        pass

    @abstractmethod
    async def generate_suggestions(
        self,
        files: List[FileMetadata],
        options: Optional[OrganizationOptions] = None,
    ) -> List[FileSuggestion]:
        """
        Analyze a list of file metadata records and produce organization suggestions.
        Must NOT read or require file contents.
        """
        pass
