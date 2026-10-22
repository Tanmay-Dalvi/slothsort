"""Validation and safety routines for filenames, paths, and collision detection."""

import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple

from backend.app.models.operation import ConflictNotice, ConflictType, FileOperation, OperationType

# Forbidden characters in filenames across POSIX and Windows/FAT32 filesystems
ILLEGAL_CHARS = set('<>:"/\\|?*\0')
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_component(name: str) -> str:
    """
    Sanitize a single path component (filename or directory name).
    Replaces illegal characters with underscores, strips trailing dots/spaces.
    """
    cleaned = "".join("_" if c in ILLEGAL_CHARS or ord(c) < 32 else c for c in name)
    cleaned = cleaned.strip(". ")
    if not cleaned or cleaned.upper() in RESERVED_NAMES:
        cleaned = f"item_{cleaned}" if cleaned else "unnamed_item"
    return cleaned[:255]


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single filename string.
    Returns (is_valid, error_message).
    """
    if not filename or not filename.strip():
        return False, "Filename cannot be empty"

    if filename in {".", ".."}:
        return False, f"Filename cannot be reserved navigation token '{filename}'"

    # Check for illegal characters and control characters
    for ch in filename:
        if ch in ILLEGAL_CHARS or ord(ch) < 32:
            return False, f"Filename contains invalid character: {repr(ch)}"

    # Check for leading/trailing spaces or trailing dots
    if filename != filename.strip():
        return False, "Filename cannot have leading or trailing whitespace"
    if filename.endswith("."):
        return False, "Filename cannot end with a period"

    # Check Windows reserved base names
    base = filename.split(".")[0].upper()
    if base in RESERVED_NAMES:
        return False, f"Filename uses reserved system device name: '{base}'"

    # Component length limit (255 bytes)
    if len(filename.encode("utf-8")) > 255:
        return False, "Filename exceeds 255 byte limit"

    return True, None


def validate_rel_path(rel_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a proposed relative path (category + filename).
    Rejects parent traversal (..), absolute paths, and invalid components.
    """
    if not rel_path or not rel_path.strip():
        return False, "Relative path cannot be empty"

    # Reject absolute paths or Windows drive letters
    if rel_path.startswith("/") or rel_path.startswith("\\"):
        return False, "Relative path cannot be absolute"
    if re.match(r"^[a-zA-Z]:", rel_path):
        return False, "Relative path cannot contain drive specifications"

    # Normalize separators
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")

    for part in parts:
        if part in {".", ""}:
            continue
        if part == "..":
            return False, "Parent directory traversal ('..') is strictly prohibited"
        is_valid, err = validate_filename(part)
        if not is_valid:
            return False, f"Invalid path component '{part}': {err}"

    return True, None


def assert_path_contained(canonical_root: Path, target_path: Path) -> None:
    """
    Assert that target_path resolves strictly within canonical_root.
    Raises ValueError on traversal escape.
    """
    resolved_target = target_path.resolve()
    resolved_root = canonical_root.resolve()
    if not resolved_target.is_relative_to(resolved_root):
        raise ValueError(
            f"Security violation: Target path '{resolved_target}' escapes root '{resolved_root}'"
        )


class PlanValidator:
    """
    Validates a set of proposed operations against security, filesystem,
    and intra-batch collision rules.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()

    def validate_operations(
        self, operations: List[FileOperation]
    ) -> List[FileOperation]:
        """
        Runs complete validation pass over operations:
        1. Source existence and containment
        2. Symlink rejection
        3. Filename and path format validation
        4. Target confinement to root
        5. Intra-batch collision detection (two files targeting same path)
        6. Filesystem collision detection (target already exists on disk)
        """
        validated_ops: List[FileOperation] = []
        target_counts: Dict[str, List[int]] = {}

        for idx, op in enumerate(operations):
            conflicts: List[ConflictNotice] = []
            raw_source_path = self.root_path / op.source_rel_path
            raw_target_path = self.root_path / op.target_rel_path

            # Check symlink on the raw path before resolving
            if raw_source_path.is_symlink():
                conflicts.append(
                    ConflictNotice(
                        conflict_type=ConflictType.SYMLINK_REJECTED,
                        message="Source is a symbolic link; operations on symlinks are prohibited",
                        conflicting_path=op.source_rel_path,
                    )
                )

            source_path = raw_source_path.resolve()
            target_path = raw_target_path.resolve()

            # 1. Source existence and containment
            try:
                assert_path_contained(self.root_path, source_path)
            except ValueError as e:
                conflicts.append(
                    ConflictNotice(
                        conflict_type=ConflictType.PATH_TRAVERSAL,
                        message=f"Source path escapes root: {str(e)}",
                        conflicting_path=op.source_rel_path,
                    )
                )

            if not raw_source_path.exists() and not raw_source_path.is_symlink():
                conflicts.append(
                    ConflictNotice(
                        conflict_type=ConflictType.SOURCE_NOT_FOUND,
                        message=f"Source file does not exist: {op.source_rel_path}",
                        conflicting_path=op.source_rel_path,
                    )
                )

            # 2. Path format and traversal validation
            is_valid_path, path_err = validate_rel_path(op.target_rel_path)
            if not is_valid_path:
                conflicts.append(
                    ConflictNotice(
                        conflict_type=ConflictType.INVALID_FILENAME,
                        message=f"Invalid target path: {path_err}",
                        conflicting_path=op.target_rel_path,
                    )
                )

            # 3. Target root confinement
            try:
                assert_path_contained(self.root_path, target_path)
            except ValueError as e:
                conflicts.append(
                    ConflictNotice(
                        conflict_type=ConflictType.PATH_TRAVERSAL,
                        message=f"Target path escapes root: {str(e)}",
                        conflicting_path=op.target_rel_path,
                    )
                )

            # 4. Check if target or any parent component is a symlink on disk
            try:
                if raw_target_path.is_symlink():
                    conflicts.append(
                        ConflictNotice(
                            conflict_type=ConflictType.SYMLINK_REJECTED,
                            message="Destination path is an existing symbolic link",
                            conflicting_path=op.target_rel_path,
                        )
                    )
            except OSError:
                pass

            # 5. Filesystem collision check
            # If target exists and is different from source, flag collision
            norm_source = op.source_rel_path.replace("\\", "/").strip("/")
            norm_target = op.target_rel_path.replace("\\", "/").strip("/")

            if norm_source != norm_target:
                if target_path.exists():
                    conflicts.append(
                        ConflictNotice(
                            conflict_type=ConflictType.FILESYSTEM_COLLISION,
                            message=f"Target file already exists on disk: {op.target_rel_path}",
                            conflicting_path=op.target_rel_path,
                        )
                    )

            # Track destination for intra-batch collisions
            target_counts.setdefault(norm_target, []).append(idx)

            # Update op with detected conflicts
            op.conflicts = conflicts
            validated_ops.append(op)

        # 6. Flag intra-batch collisions (multiple files targeting identical destination)
        for target_rel, indices in target_counts.items():
            if len(indices) > 1:
                for idx in indices:
                    op = validated_ops[idx]
                    # Only flag if not a self-mapping KEEP for all
                    op.conflicts.append(
                        ConflictNotice(
                            conflict_type=ConflictType.INTRA_BATCH_COLLISION,
                            message=f"Duplicate destination: {len(indices)} files are mapped to '{target_rel}'",
                            conflicting_path=target_rel,
                        )
                    )

        return validated_ops
