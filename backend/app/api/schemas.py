"""Request and response schemas for REST API endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.models.operation import FileOperation
from backend.app.models.plan import OrganizationOptions


class ScanRequest(BaseModel):
    """Payload for folder scanning endpoint."""
    folder_path: str = Field(
        ...,
        description="Absolute path to the user-selected folder to scan",
        examples=["/home/user/Downloads"]
    )
    max_depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Maximum directory traversal depth (default configured in backend)"
    )


class GeneratePlanRequest(BaseModel):
    """Payload for plan generation endpoint."""
    folder_path: str = Field(
        ...,
        description="Absolute path to the target folder",
        examples=["/home/user/Downloads"]
    )
    provider_id: Optional[str] = Field(
        default="ollama",
        description="Explicitly selected AI provider ('mock', 'ollama', or 'gemini')",
        examples=["ollama"]
    )
    options: Optional[OrganizationOptions] = Field(
        default_factory=OrganizationOptions,
        description="User organization preferences and naming conventions"
    )


class ValidatePlanRequest(BaseModel):
    """Payload for re-validating a user-edited organization plan."""
    plan_id: str = Field(
        ...,
        description="Original plan identifier returned by /api/plan/generate",
        examples=["plan_20261022_120000_abc123"]
    )
    operations: List[FileOperation] = Field(
        ...,
        description="List of proposed operations, potentially modified by the user"
    )


class ExecutePlanRequest(BaseModel):
    """Payload for plan execution endpoint."""
    plan_id: str = Field(
        ...,
        description="Plan ID to execute",
        examples=["plan_20261022_120000_abc123"]
    )
    approved_op_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Explicit list of operation IDs approved for execution by the user"
    )


class UndoRequest(BaseModel):
    """Payload for rollback/undo endpoint."""
    manifest_id: str = Field(
        ...,
        pattern=r"^man_[a-zA-Z0-9_\-]+$",
        description="Unique identifier of the execution manifest to revert",
        examples=["man_20261022_120000_8f9a"]
    )
