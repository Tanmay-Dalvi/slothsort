"""Models for AI suggestions and organization plans."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.models.operation import FileOperation


class FileSuggestion(BaseModel):
    """Raw suggestion produced by an AI provider for a single file."""
    file_id: str = Field(description="Corresponding FileMetadata.id")
    suggested_category: str = Field(description="Category or subdirectory (e.g. 'Documents', 'Finance/Receipts')")
    suggested_filename: str = Field(description="Normalized filename including extension")
    reasoning: str = Field(default="", description="Optional human-readable explanation")


class OrganizationOptions(BaseModel):
    """Parameters controlling plan generation."""
    max_categories: int = Field(default=6, ge=1, le=20)
    naming_convention: str = Field(default="preserve")  # "preserve", "clean_snake", "clean_kebab"
    custom_instructions: Optional[str] = None


def generate_plan_id() -> str:
    """Generate a unique plan ID."""
    return f"plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


class OrganizationPlan(BaseModel):
    """Preview-only organization plan containing validated operations."""
    plan_id: str = Field(default_factory=generate_plan_id)
    root_path: str = Field(description="Canonical absolute path of selected directory")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 creation timestamp"
    )
    provider_used: str = Field(default="mock", description="Identifier of provider used")
    total_files: int = Field(default=0, ge=0, description="Total files evaluated")
    operations: List[FileOperation] = Field(default_factory=list)
    conflicts_detected: int = Field(default=0, ge=0)
    is_validated: bool = Field(default=False)
    requires_approval: bool = Field(default=True, description="Strict safety requirement")
