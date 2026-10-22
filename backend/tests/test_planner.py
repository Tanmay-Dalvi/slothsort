"""Tests for preview-only DeterministicOrganizationPlanner."""

from pathlib import Path
import pytest

from backend.app.engine.planner import DeterministicOrganizationPlanner
from backend.app.engine.scanner import SafeFolderScanner
from backend.app.models.operation import OperationType
from backend.app.models.plan import FileSuggestion


def test_planner_preview_does_not_mutate_disk(sample_dir: Path):
    """
    Critical Safety Test:
    Generating an organization plan must be strictly read-only.
    Directory contents and file modification times must not change.
    """
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    # Record filesystem snapshot before planning
    files_before = {p.name: p.stat().st_mtime for p in sample_dir.rglob("*") if p.is_file()}

    suggestions = [
        FileSuggestion(
            file_id=f.id,
            suggested_category="OrganizedDocs",
            suggested_filename=f"clean_{f.filename}",
            reasoning="Test rule",
        )
        for f in scan_result.files
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(
        files=scan_result.files,
        suggestions=suggestions,
        provider_used="mock",
    )

    # Record filesystem snapshot after planning
    files_after = {p.name: p.stat().st_mtime for p in sample_dir.rglob("*") if p.is_file()}

    # Assert exact filesystem equivalence
    assert files_before == files_after
    assert not (sample_dir / "OrganizedDocs").exists()

    # Assert plan structure
    assert plan.total_files == len(scan_result.files)
    assert plan.is_validated is True
    assert plan.requires_approval is True
    assert len(plan.operations) == len(scan_result.files)


def test_planner_unsuggested_files_kept_in_place(sample_dir: Path):
    """Verifies that files with no suggestions default to KEEP in their current location."""
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    # Only provide suggestion for 1 file
    first_file = scan_result.files[0]
    suggestions = [
        FileSuggestion(
            file_id=first_file.id,
            suggested_category="TargetCategory",
            suggested_filename="renamed_first.ext",
        )
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    keep_ops = [op for op in plan.operations if op.op_type == OperationType.KEEP]
    assert len(keep_ops) == len(scan_result.files) - 1

    first_op = next(op for op in plan.operations if op.file_id == first_file.id)
    assert first_op.op_type != OperationType.KEEP
    assert first_op.target_rel_path == "TargetCategory/renamed_first.ext"
