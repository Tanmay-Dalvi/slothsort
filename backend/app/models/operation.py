"""Models representing file operations, collisions, and statuses."""

from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """The type of disk change proposed for a file."""
    MOVE = "MOVE"
    RENAME = "RENAME"
    MOVE_AND_RENAME = "MOVE_AND_RENAME"
    KEEP = "KEEP"


class OperationStatus(str, Enum):
    """The lifecycle status of an operation."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class ConflictType(str, Enum):
    """Categorization of safety or collision conflicts."""
    NONE = "NONE"
    INTRA_BATCH_COLLISION = "INTRA_BATCH_COLLISION"    # Two files targeting the same path
    FILESYSTEM_COLLISION = "FILESYSTEM_COLLISION"      # Target already exists on disk
    PATH_TRAVERSAL = "PATH_TRAVERSAL"                  # Target attempts to escape root
    SYMLINK_REJECTED = "SYMLINK_REJECTED"              # Source or target involves a symlink
    INVALID_FILENAME = "INVALID_FILENAME"              # Illegal characters, reserved name
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"              # Source file does not exist
    PERMISSION_DENIED = "PERMISSION_DENIED"            # Lack of write permissions


class ConflictNotice(BaseModel):
    """Details regarding an operation conflict or safety violation."""
    conflict_type: ConflictType
    message: str
    conflicting_path: Optional[str] = None


def generate_operation_id() -> str:
    """Generate a stable, unique operation ID."""
    return f"op_{uuid.uuid4().hex[:12]}"


class FileOperation(BaseModel):
    """A proposed, validated, or executed operation for a single file."""
    op_id: str = Field(default_factory=generate_operation_id)
    file_id: str = Field(description="Matches corresponding FileMetadata.id")
    source_rel_path: str = Field(description="Current relative path from root")
    target_rel_path: str = Field(description="Target relative path from root")
    op_type: OperationType = Field(default=OperationType.MOVE)
    status: OperationStatus = Field(default=OperationStatus.PENDING)
    is_approved: bool = Field(default=True, description="Whether user has approved this move")
    conflicts: List[ConflictNotice] = Field(default_factory=list)

    @property
    def has_conflict(self) -> bool:
        """True if any conflicts are attached to this operation."""
        return len(self.conflicts) > 0
