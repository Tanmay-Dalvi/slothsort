"""Tests for SafePlanExecutor."""

from pathlib import Path
import pytest

from backend.app.engine.executor import SafePlanExecutor
from backend.app.engine.planner import DeterministicOrganizationPlanner
from backend.app.engine.scanner import SafeFolderScanner
from backend.app.models.manifest import ExecutionStatus
from backend.app.models.operation import FileOperation, OperationStatus, OperationType, generate_operation_id
from backend.app.models.plan import FileSuggestion, OrganizationPlan


def test_executor_refuses_unvalidated_plan(sample_dir: Path, temp_manifest_dir: Path):
    """Verifies that an unvalidated plan is rejected without executing any operations."""
    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)

    plan = OrganizationPlan(
        root_path=str(sample_dir),
        is_validated=False,  # Unvalidated
        operations=[
            FileOperation(
                op_id=generate_operation_id(),
                file_id="f1",
                source_rel_path="notes.txt",
                target_rel_path="Docs/notes.txt",
            )
        ],
    )

    result = executor.execute_plan(plan)
    assert result.status == ExecutionStatus.FAILED
    assert result.executed_count == 0
    assert "unvalidated" in result.errors[0]
    assert (sample_dir / "notes.txt").exists()


def test_executor_requires_approval(sample_dir: Path, temp_manifest_dir: Path):
    """Verifies that unapproved operations are skipped and marked REJECTED."""
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    suggestions = [
        FileSuggestion(
            file_id=scan_result.files[0].id,
            suggested_category="Documents",
            suggested_filename="moved.pdf",
        )
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    # Explicitly set is_approved = False
    for op in plan.operations:
        op.is_approved = False

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    result = executor.execute_plan(plan)

    assert result.executed_count == 0
    assert not (sample_dir / "Documents" / "moved.pdf").exists()


def test_executor_successful_moves_and_manifest(sample_dir: Path, temp_manifest_dir: Path):
    """Verifies successful moves, folder creation, and manifest persistence."""
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    pdf_file = next(f for f in scan_result.files if f.filename == "invoice_2026.pdf")
    suggestions = [
        FileSuggestion(
            file_id=pdf_file.id,
            suggested_category="Finance/Invoices",
            suggested_filename="2026_invoice.pdf",
        )
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    result = executor.execute_plan(plan)

    assert result.status == ExecutionStatus.SUCCESS
    assert result.executed_count == 1
    assert result.undo_manifest_id is not None

    # Check filesystem
    assert not (sample_dir / "invoice_2026.pdf").exists()
    assert (sample_dir / "Finance" / "Invoices" / "2026_invoice.pdf").exists()

    # Check manifest loaded from disk
    manifest = executor.manifest_storage.load_manifest(result.undo_manifest_id)
    assert manifest is not None
    assert len(manifest.steps) == 1
    assert manifest.steps[0].file_size_bytes > 0


def test_executor_blocks_conflicted_operations(sample_dir: Path, temp_manifest_dir: Path):
    """Verifies operations with unresolved conflicts are blocked from execution."""
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    # Intentionally create collision: move invoice_2026.pdf to notes.txt
    pdf_file = next(f for f in scan_result.files if f.filename == "invoice_2026.pdf")
    suggestions = [
        FileSuggestion(
            file_id=pdf_file.id,
            suggested_category=".",
            suggested_filename="notes.txt",
        )
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)
    assert plan.conflicts_detected > 0

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    result = executor.execute_plan(plan)

    # Should fail or partially fail without overwriting notes.txt
    assert (sample_dir / "invoice_2026.pdf").exists()
    assert (sample_dir / "notes.txt").exists()


def test_executor_partial_failure_handling(sample_dir: Path, temp_manifest_dir: Path):
    """
    Verifies that when one operation succeeds and another fails,
    the overall status is PARTIAL_FAILURE, errors are reported,
    and the manifest records only the succeeded move.
    """
    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)

    # Op 1: valid move (photo.jpg -> Images/photo.jpg)
    op1 = FileOperation(
        op_id=generate_operation_id(),
        file_id="f1",
        source_rel_path="photo.jpg",
        target_rel_path="Images/photo.jpg",
        op_type=OperationType.MOVE,
        is_approved=True,
    )

    # Op 2: source file does not exist (will fail)
    op2 = FileOperation(
        op_id=generate_operation_id(),
        file_id="f2",
        source_rel_path="nonexistent_source.pdf",
        target_rel_path="Docs/nonexistent_source.pdf",
        op_type=OperationType.MOVE,
        is_approved=True,
    )

    plan = OrganizationPlan(
        root_path=str(sample_dir),
        is_validated=True,
        total_files=2,
        operations=[op1, op2],
    )

    result = executor.execute_plan(plan)

    assert result.status == ExecutionStatus.PARTIAL_FAILURE
    assert result.executed_count == 1
    assert result.failed_count == 1
    assert len(result.errors) == 1
    assert result.undo_manifest_id is not None

    # Check that op1 succeeded and op2 failed
    assert (sample_dir / "Images" / "photo.jpg").exists()
    assert not (sample_dir / "photo.jpg").exists()

    manifest = executor.manifest_storage.load_manifest(result.undo_manifest_id)
    assert len(manifest.steps) == 1
    assert manifest.steps[0].op_id == op1.op_id
