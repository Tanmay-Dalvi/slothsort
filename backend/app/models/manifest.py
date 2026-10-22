"""Models for undo manifests and execution tracking."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class UndoStatus(str, Enum):
    """Lifecycle status of an undo manifest."""
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"
    PARTIALLY_ROLLED_BACK = "PARTIALLY_ROLLED_BACK"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class ExecutionStatus(str, Enum):
    """Result status of batch execution."""
    SUCCESS = "SUCCESS"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"


def generate_manifest_id() -> str:
    """Generate a unique manifest ID."""
    return f"man_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


class ExecutedStep(BaseModel):
    """Record of a successfully executed move operation."""
    step_id: int = Field(ge=1, description="1-based sequence index")
    op_id: str = Field(description="Corresponding FileOperation.op_id")
    file_id: str = Field(description="Original FileMetadata.id")
    source_abs_path: str = Field(description="Canonical path where file originated")
    target_abs_path: str = Field(description="Canonical path where file was moved")
    file_size_bytes: int = Field(ge=0, description="Size in bytes at time of execution")
    mtime: float = Field(description="Modification timestamp at time of move")
    created_directories: List[str] = Field(
        default_factory=list,
        description="Directories newly created to accommodate target file (in leaf-to-parent order)"
    )
    executed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class UndoManifest(BaseModel):
    """Complete transaction log of an executed batch."""
    manifest_id: str = Field(default_factory=generate_manifest_id)
    plan_id: str = Field(description="Original OrganizationPlan ID")
    root_path: str = Field(description="Canonical absolute path to folder")
    executed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    provider: str = Field(default="mock")
    steps: List[ExecutedStep] = Field(default_factory=list)
    status: UndoStatus = Field(default=UndoStatus.APPLIED)


class ExecutionResult(BaseModel):
    """Summary of batch execution."""
    batch_id: str
    plan_id: str
    status: ExecutionStatus
    executed_count: int = 0
    failed_count: int = 0
    undo_manifest_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


class RollbackResult(BaseModel):
    """Summary of an undo operation."""
    manifest_id: str
    status: UndoStatus
    restored_count: int = 0
    failed_count: int = 0
    errors: List[str] = Field(default_factory=list)
