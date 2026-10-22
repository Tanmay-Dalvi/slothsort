"""Safe folder scanner with memory-efficient traversal and symlink guardrails."""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Generator, List, Optional, Set, Tuple, Union

from backend.app.config import settings
from backend.app.models.file import (
    FileMetadata,
    ScanError,
    ScanResult,
    SkippedFile,
    generate_file_id,
)


class SafeFolderScanner:
    """
    Recursively scans a specified root directory.

    Guarantees:
    - Never follows symbolic links.
    - Never reads file content (metadata only).
    - Skips known system and build directories (e.g. .git, node_modules).
    - Catches and reports all permission and filesystem errors explicitly.
    """

    def __init__(
        self,
        ignored_dir_names: Optional[Set[str]] = None,
        max_depth: Optional[int] = None,
    ):
        self.ignored_dir_names = (
            ignored_dir_names if ignored_dir_names is not None else settings.IGNORED_DIR_NAMES
        )
        self.max_depth = max_depth if max_depth is not None else settings.MAX_SCAN_DEPTH

    def scan(self, root: Union[str, Path]) -> ScanResult:
        """
        Executes a scan over the provided directory and returns an aggregate ScanResult.
        Raises ValueError if root does not exist or is not a directory.
        """
        root_path = Path(root).resolve()
        if not root_path.exists():
            raise ValueError(f"Target directory does not exist: {root_path}")
        if not root_path.is_dir():
            raise ValueError(f"Target path is not a directory: {root_path}")
        if root_path.is_symlink():
            raise ValueError(f"Target root directory cannot be a symbolic link: {root_path}")

        files: List[FileMetadata] = []
        skipped_files: List[SkippedFile] = []
        errors: List[ScanError] = []
        total_bytes = 0

        for item, skipped, err in self.iter_scan(root_path):
            if item is not None:
                files.append(item)
                total_bytes += item.size_bytes
            if skipped is not None:
                skipped_files.append(skipped)
            if err is not None:
                errors.append(err)

        return ScanResult(
            root_path=str(root_path),
            total_files=len(files),
            total_bytes=total_bytes,
            files=files,
            skipped_files=skipped_files,
            errors=errors,
        )

    def iter_scan(
        self, root_path: Path
    ) -> Generator[Tuple[Optional[FileMetadata], Optional[SkippedFile], Optional[ScanError]], None, None]:
        """
        Memory-efficient generator yielding (FileMetadata, SkippedFile, ScanError).
        One of the tuple elements will be non-None per yield.
        """
        canonical_root = root_path.resolve()
        root_depth = len(canonical_root.parts)

        # os.walk with followlinks=False guarantees no symlink following
        for current_dir_str, dirnames, filenames in os.walk(str(canonical_root), followlinks=False):
            current_dir = Path(current_dir_str)
            current_depth = len(current_dir.parts) - root_depth

            # Enforce max depth
            if current_depth >= self.max_depth:
                dirnames.clear()
                continue

            # In-place prune ignored directories (.git, node_modules, etc.)
            pruned_dirs = []
            for d in list(dirnames):
                dir_path = current_dir / d
                try:
                    if dir_path.is_symlink():
                        yield (
                            None,
                            SkippedFile(
                                path=str(dir_path.relative_to(canonical_root)),
                                reason="Symbolic link directory skipped",
                            ),
                            None,
                        )
                        pruned_dirs.append(d)
                    elif d in self.ignored_dir_names:
                        yield (
                            None,
                            SkippedFile(
                                path=str(dir_path.relative_to(canonical_root)),
                                reason=f"Ignored system/build directory ({d})",
                            ),
                            None,
                        )
                        pruned_dirs.append(d)
                except OSError as e:
                    yield (
                        None,
                        None,
                        ScanError(
                            path=str(dir_path),
                            error_message=f"Filesystem error checking directory {d}: {str(e)}",
                        ),
                    )
                    pruned_dirs.append(d)

            for p in pruned_dirs:
                dirnames.remove(p)

            # Process files in current directory
            for f in filenames:
                file_path = current_dir / f
                try:
                    rel_path = str(file_path.relative_to(canonical_root))
                except ValueError:
                    yield (
                        None,
                        None,
                        ScanError(
                            path=str(file_path),
                            error_message="File path is not relative to root",
                        ),
                    )
                    continue

                # Check for symlink file
                try:
                    if file_path.is_symlink():
                        yield (
                            None,
                            SkippedFile(
                                path=rel_path,
                                reason="Symbolic link file skipped for safety",
                            ),
                            None,
                        )
                        continue
                except OSError as e:
                    yield (
                        None,
                        None,
                        ScanError(
                            path=str(file_path),
                            error_message=f"Error checking symlink status: {str(e)}",
                        ),
                    )
                    continue

                # Collect metadata safely
                try:
                    st = file_path.stat(follow_symlinks=False)
                    mtime_dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                    ext = file_path.suffix.lstrip(".").lower()

                    metadata = FileMetadata(
                        id=generate_file_id(rel_path),
                        original_rel_path=rel_path,
                        filename=file_path.name,
                        extension=ext,
                        size_bytes=st.st_size,
                        modified_at=mtime_dt.isoformat(),
                        is_symlink=False,
                        is_accessible=True,
                    )
                    yield (metadata, None, None)
                except (PermissionError, OSError) as e:
                    yield (
                        None,
                        SkippedFile(
                            path=rel_path,
                            reason=f"Inaccessible file (PermissionError/OSError: {e})",
                        ),
                        None,
                    )
