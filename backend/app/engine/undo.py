"""Safe undo and rollback engine with pre-validation of restoration destinations."""

import os
from pathlib import Path
import shutil
from typing import List, Optional, Union

from backend.app.engine.manifest import ManifestStorage
from backend.app.engine.validator import assert_path_contained
from backend.app.models.manifest import (
    RollbackResult,
    UndoManifest,
    UndoStatus,
)


class UndoEngine:
    """
    Rolls back executed organization batches in reverse chronological order.

    Safety guarantees:
    1. Validates destination availability before moving files back.
    2. Never overwrites a file if something was created at the original location.
    3. Prunes only the exact empty directories created by the plan (never non-empty).
    4. Reports accurate partial failure statuses instead of claiming full reversibility.
    """

    def __init__(self, manifest_dir: Optional[Path] = None):
        self.manifest_storage = ManifestStorage(manifest_dir)

    def rollback(self, manifest_or_id: Union[UndoManifest, str]) -> RollbackResult:
        """
        Executes inverse rollback for the given manifest.
        """
        if isinstance(manifest_or_id, str):
            manifest = self.manifest_storage.load_manifest(manifest_or_id)
            if manifest is None:
                return RollbackResult(
                    manifest_id=manifest_or_id,
                    status=UndoStatus.ROLLBACK_FAILED,
                    restored_count=0,
                    failed_count=0,
                    errors=[f"Manifest with ID '{manifest_or_id}' was not found"],
                )
        else:
            manifest = manifest_or_id

        if manifest.status == UndoStatus.ROLLED_BACK:
            return RollbackResult(
                manifest_id=manifest.manifest_id,
                status=UndoStatus.ROLLED_BACK,
                restored_count=0,
                failed_count=0,
                errors=["This batch has already been rolled back."],
            )

        restored_count = 0
        failed_count = 0
        errors: List[str] = []

        # Process steps in reverse chronological order
        reversed_steps = list(reversed(manifest.steps))

        canonical_root = Path(manifest.root_path).resolve()

        for step in reversed_steps:
            target_path = Path(step.target_abs_path)
            source_path = Path(step.source_abs_path)

            # Security Check: Target and source must strictly remain within manifest root
            try:
                assert_path_contained(canonical_root, source_path)
                assert_path_contained(canonical_root, target_path)
            except ValueError as e:
                failed_count += 1
                errors.append(f"Security containment failure in step {step.step_id}: {str(e)}")
                continue

            # Check 1: Target file must still exist where we put it
            if not target_path.exists():
                failed_count += 1
                errors.append(
                    f"Step {step.step_id} cannot be rolled back: moved file at '{target_path}' is missing or moved externally"
                )
                continue

            # Check 2: Original source path must NOT be occupied by an existing file
            if source_path.exists():
                failed_count += 1
                errors.append(
                    f"Step {step.step_id} collision: original location '{source_path}' is already occupied by an existing file"
                )
                continue

            # Perform the reverse move
            try:
                # Ensure original directory exists
                source_path.parent.mkdir(parents=True, exist_ok=True)

                # Move back safely
                shutil.move(str(target_path), str(source_path))
                restored_count += 1

                # Clean up empty directories created by this step (leaf-to-parent)
                for created_dir_str in step.created_directories:
                    created_dir = Path(created_dir_str)
                    try:
                        # Directory must be strictly within root and not root itself
                        assert_path_contained(canonical_root, created_dir)
                        if created_dir.resolve() != canonical_root and created_dir.exists() and created_dir.is_dir():
                            os.rmdir(created_dir)
                    except (ValueError, OSError):
                        # Non-empty directory or security assertion; leave safely intact
                        pass

            except Exception as e:
                failed_count += 1
                errors.append(
                    f"Step {step.step_id} failed during reverse move ({target_path} -> {source_path}): {str(e)}"
                )

        # Determine updated manifest status
        if failed_count == 0 and restored_count > 0:
            final_status = UndoStatus.ROLLED_BACK
        elif restored_count > 0 and failed_count > 0:
            final_status = UndoStatus.PARTIALLY_ROLLED_BACK
        elif failed_count > 0 and restored_count == 0:
            final_status = UndoStatus.ROLLBACK_FAILED
        else:
            final_status = UndoStatus.ROLLED_BACK

        manifest.status = final_status
        self.manifest_storage.save_manifest(manifest)

        return RollbackResult(
            manifest_id=manifest.manifest_id,
            status=final_status,
            restored_count=restored_count,
            failed_count=failed_count,
            errors=errors,
        )
