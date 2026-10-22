"""Deterministic mock AI provider for testing and offline development."""

from pathlib import Path
import re
from typing import Dict, List, Optional

from backend.app.models.file import FileMetadata
from backend.app.models.plan import FileSuggestion, OrganizationOptions
from backend.app.providers.base import AIProvider, ProviderHealth

EXTENSION_MAP: Dict[str, str] = {
    # Documents
    "pdf": "Documents",
    "docx": "Documents",
    "doc": "Documents",
    "txt": "Documents",
    "md": "Documents",
    "rtf": "Documents",
    "csv": "Documents",
    "xlsx": "Documents",
    # Images
    "png": "Images",
    "jpg": "Images",
    "jpeg": "Images",
    "gif": "Images",
    "svg": "Images",
    "webp": "Images",
    # Archives
    "zip": "Archives",
    "tar": "Archives",
    "gz": "Archives",
    "7z": "Archives",
    "rar": "Archives",
    # Code & Development
    "py": "Development",
    "ts": "Development",
    "tsx": "Development",
    "js": "Development",
    "json": "Development",
    "yaml": "Development",
    "yml": "Development",
    "sh": "Development",
    "html": "Development",
    "css": "Development",
    # Media
    "mp3": "Media",
    "wav": "Media",
    "flac": "Media",
    "mp4": "Media",
    "mkv": "Media",
    "mov": "Media",
}


class MockAIProvider(AIProvider):
    """
    Deterministic provider producing consistent categorization and renaming rules.
    Used for unit testing, CI runs, and environments without active LLMs.
    """

    @property
    def provider_id(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "deterministic-rules-v1"

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            is_available=True,
            provider_name="Deterministic Mock Provider",
            model_name=self.default_model,
            latency_ms=0.5,
            is_cloud=False,
            privacy_notice="100% Local Heuristics (No external network traffic)",
        )

    async def generate_suggestions(
        self,
        files: List[FileMetadata],
        options: Optional[OrganizationOptions] = None,
    ) -> List[FileSuggestion]:
        opt = options or OrganizationOptions()
        suggestions: List[FileSuggestion] = []

        for f in files:
            ext = f.extension.lower()
            category = EXTENSION_MAP.get(ext, "Miscellaneous")

            # Determine proposed filename
            base_name = Path(f.filename).stem
            extension_part = f".{ext}" if ext else ""

            if opt.naming_convention == "clean_snake":
                cleaned_base = re.sub(r"[\s\-_]+", "_", base_name).strip("_").lower()
                suggested_filename = f"{cleaned_base}{extension_part}"
            elif opt.naming_convention == "clean_kebab":
                cleaned_base = re.sub(r"[\s\-_]+", "-", base_name).strip("-").lower()
                suggested_filename = f"{cleaned_base}{extension_part}"
            else:
                suggested_filename = f.filename

            suggestions.append(
                FileSuggestion(
                    file_id=f.id,
                    suggested_category=category,
                    suggested_filename=suggested_filename,
                    reasoning=f"Matched extension '.{ext}' to category '{category}'",
                )
            )

        return suggestions
