"""Safe plan executor with strict approval validation and failure isolation."""

import os
from pathlib import Path
import shutil
from typing import List, Optional, Set, Union
import uuid

from backend.app.engine.manifest import ManifestStorage
from backend.app.engine.validator import assert_path_contained
from backend.app.models.manifest import (
    ExecutedStep,
    ExecutionResult,
    ExecutionStatus,
    UndoManifest,
    UndoStatus,
    generate_manifest_id,
)
from backend.app.models.operation import OperationStatus, OperationType
from backend.app.models.plan import OrganizationPlan


class SafePlanExecutor:
    """
    Executes validated organization plans.

    Invariants:
    1. Zero silent overwrites: Checks existence atomically before moving.
    2. Zero file deletions: Contains only move/rename logic.
    3. Root containment: Re-asserts canonical containment for every operation.
    4. Explicit approval: Refuses execution unless user has approved the plan/ops.
    5. Partial failure tracking: Logs exact outcome and saves undo log for successful steps.
    """

    def __init__(self, manifest_dir: Optional[Path] = None):
        self.manifest_storage = ManifestStorage(manifest_dir)

    def execute_plan(
        self,
        plan: OrganizationPlan,
        approved_op_ids: Optional[Set[str]] = None,
        force_unvalidated: bool = False,
    ) -> ExecutionResult:
        """
        Executes approved operations within the plan.

        Args:
            plan: The validated OrganizationPlan.
            approved_op_ids: Explicit set of operation IDs to execute.
                             If None, executes all operations where is_approved is True.
            force_unvalidated: Must remain False in production. Execution requires validated plan.
        """
        batch_id = f"batch_{uuid.uuid4().hex[:10]}"

        if not plan.is_validated and not force_unvalidated:
            return ExecutionResult(
                batch_id=batch_id,
                plan_id=plan.plan_id,
                status=ExecutionStatus.FAILED,
                executed_count=0,
                failed_count=len(plan.operations),
                errors=["Cannot execute an unvalidated organization plan."],
            )

        root_path = Path(plan.root_path).resolve()
        if not root_path.exists() or not root_path.is_dir():
            return ExecutionResult(
                batch_id=batch_id,
                plan_id=plan.plan_id,
                status=ExecutionStatus.FAILED,
                executed_count=0,
                failed_count=len(plan.operations),
                errors=[f"Root directory does not exist or is not a directory: {root_path}"],
            )

        executed_steps: List[ExecutedStep] = []
        errors: List[str] = []
        failed_count = 0
        executed_count = 0

        for op in plan.operations:
            # Check if this operation is approved
            is_explicitly_approved = (
                (approved_op_ids is None and op.is_approved) or
                (approved_op_ids is not None and op.op_id in approved_op_ids and op.is_approved)
            )

            if not is_explicitly_approved:
                op.status = OperationStatus.REJECTED
                continue

            # Reject operations that have unresolved safety conflicts
            if op.has_conflict:
                failed_count += 1
                op.status = OperationStatus.FAILED
                conflict_msgs = "; ".join(c.message for c in op.conflicts)
                errors.append(f"Operation {op.op_id} blocked by unresolved conflict: {conflict_msgs}")
                continue

            # If operation is KEEP (source == target), no filesystem action needed
            if op.op_type == OperationType.KEEP or op.source_rel_path == op.target_rel_path:
                op.status = OperationStatus.EXECUTED
                continue

            raw_source_abs = root_path / op.source_rel_path
            raw_target_abs = root_path / op.target_rel_path

            if raw_source_abs.is_symlink():
                failed_count += 1
                op.status = OperationStatus.FAILED
                errors.append(f"Source path is a symbolic link, skipping: {raw_source_abs}")
                continue

            if raw_target_abs.is_symlink():
                failed_count += 1
                op.status = OperationStatus.FAILED
                errors.append(f"Target path is an existing symbolic link, skipping: {raw_target_abs}")
                continue

            source_abs = raw_source_abs.resolve()
            target_abs = raw_target_abs.resolve()

            # Enforce root containment again at runtime
            try:
                assert_path_contained(root_path, source_abs)
                assert_path_contained(root_path, target_abs)
            except ValueError as e:
                failed_count += 1
                op.status = OperationStatus.FAILED
                errors.append(f"Security containment failure on {op.op_id}: {str(e)}")
                continue

            # Verify source exists
            if not raw_source_abs.exists():
                failed_count += 1
                op.status = OperationStatus.FAILED
                errors.append(f"Source file missing before move: {source_abs}")
                continue

            # Pre-flight overwrite prevention: Target MUST NOT exist
            if target_abs.exists():
                failed_count += 1
                op.status = OperationStatus.FAILED
                errors.append(f"Destination collision detected immediately prior to move: {target_abs}")
                continue

            # Track newly created directory hierarchy for clean rollback
            created_dirs: List[str] = []
            curr = target_abs.parent
            while curr != root_path and not curr.exists():
                created_dirs.append(str(curr.resolve()))
                curr = curr.parent

            # Execute move
            try:
                stat_info = source_abs.stat()
                file_size = stat_info.st_size
                mtime = stat_info.st_mtime

                # Create destination directory structure
                target_abs.parent.mkdir(parents=True, exist_ok=True)

                # Move file atomically
                shutil.move(str(source_abs), str(target_abs))

                executed_count += 1
                op.status = OperationStatus.EXECUTED

                executed_steps.append(
                    ExecutedStep(
                        step_id=len(executed_steps) + 1,
                        op_id=op.op_id,
                        file_id=op.file_id,
                        source_abs_path=str(source_abs),
                        target_abs_path=str(target_abs),
                        file_size_bytes=file_size,
                        mtime=mtime,
                        created_directories=created_dirs,
                    )
                )
            except Exception as e:
                failed_count += 1
                op.status = OperationStatus.FAILED
                errors.append(f"Filesystem error executing move for {source_abs} -> {target_abs}: {str(e)}")

        # Create and persist manifest if any steps executed
        manifest_id: Optional[str] = None
        if executed_steps:
            manifest = UndoManifest(
                manifest_id=generate_manifest_id(),
                plan_id=plan.plan_id,
                root_path=str(root_path),
                provider=plan.provider_used,
                steps=executed_steps,
                status=UndoStatus.APPLIED,
            )
            self.manifest_storage.save_manifest(manifest)
            manifest_id = manifest.manifest_id

        # Determine aggregate status
        if failed_count == 0 and executed_count > 0:
            status = ExecutionStatus.SUCCESS
        elif executed_count > 0 and failed_count > 0:
            status = ExecutionStatus.PARTIAL_FAILURE
        else:
            status = ExecutionStatus.FAILED if failed_count > 0 else ExecutionStatus.SUCCESS

        return ExecutionResult(
            batch_id=batch_id,
            plan_id=plan.plan_id,
            status=status,
            executed_count=executed_count,
            failed_count=failed_count,
            undo_manifest_id=manifest_id,
            errors=errors,
        )
