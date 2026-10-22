"""File metadata and scan result models."""

from datetime import datetime, timezone
import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field


def generate_file_id(rel_path: str) -> str:
    """Generate a stable, deterministic ID from relative POSIX path."""
    norm_path = rel_path.strip().replace("\\", "/")
    return hashlib.sha256(norm_path.encode("utf-8")).hexdigest()[:16]


class FileMetadata(BaseModel):
    """Metadata for a scanned file. Contains no file content."""
    id: str = Field(description="Deterministic 16-hex ID derived from relative path")
    original_rel_path: str = Field(description="POSIX relative path from scan root")
    filename: str = Field(description="Base filename including extension")
    extension: str = Field(description="Lowercase file extension without leading dot")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    modified_at: str = Field(description="ISO-8601 modified timestamp")
    is_symlink: bool = Field(default=False, description="Whether the entry is a symlink")
    is_accessible: bool = Field(default=True, description="Whether file read metadata succeeded")


class SkippedFile(BaseModel):
    """Record of an entry that was skipped during scanning."""
    path: str = Field(description="Relative or absolute path of skipped entry")
    reason: str = Field(description="Human-readable skip reason (e.g. symlink, system dir)")


class ScanError(BaseModel):
    """Record of an unexpected error during directory scanning."""
    path: str = Field(description="Path where error occurred")
    error_message: str = Field(description="Exact error message")


class ScanResult(BaseModel):
    """Aggregate result of a directory scan."""
    root_path: str = Field(description="Canonical absolute path to scanned directory")
    scanned_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp of scan"
    )
    total_files: int = Field(ge=0, description="Count of successfully scanned files")
    total_bytes: int = Field(ge=0, description="Cumulative size of scanned files in bytes")
    files: List[FileMetadata] = Field(default_factory=list)
    skipped_files: List[SkippedFile] = Field(default_factory=list)
    errors: List[ScanError] = Field(default_factory=list)
