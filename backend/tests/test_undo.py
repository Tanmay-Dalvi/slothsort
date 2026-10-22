"""Tests for UndoEngine and restoration safety."""

from pathlib import Path
import pytest

from backend.app.engine.executor import SafePlanExecutor
from backend.app.engine.planner import DeterministicOrganizationPlanner
from backend.app.engine.scanner import SafeFolderScanner
from backend.app.engine.undo import UndoEngine
from backend.app.models.manifest import UndoStatus
from backend.app.models.plan import FileSuggestion


def test_undo_restores_original_state_and_cleans_dirs(sample_dir: Path, temp_manifest_dir: Path):
    """
    Verifies that rollback restores files to their exact original paths
    and deletes newly created empty parent directories.
    """
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    # Move 2 files into new folders
    f1 = next(f for f in scan_result.files if f.filename == "invoice_2026.pdf")
    f2 = next(f for f in scan_result.files if f.filename == "photo.jpg")

    suggestions = [
        FileSuggestion(file_id=f1.id, suggested_category="Docs/Invoices", suggested_filename="inv.pdf"),
        FileSuggestion(file_id=f2.id, suggested_category="Media/Pics", suggested_filename="pic.jpg"),
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    exec_result = executor.execute_plan(plan)
    assert exec_result.undo_manifest_id is not None

    # Assert moved state
    assert not (sample_dir / "invoice_2026.pdf").exists()
    assert (sample_dir / "Docs" / "Invoices" / "inv.pdf").exists()

    # Now execute undo
    undo_engine = UndoEngine(manifest_dir=temp_manifest_dir)
    rollback_result = undo_engine.rollback(exec_result.undo_manifest_id)

    assert rollback_result.status == UndoStatus.ROLLED_BACK
    assert rollback_result.restored_count == 2
    assert rollback_result.failed_count == 0

    # Files must be back in their original locations
    assert (sample_dir / "invoice_2026.pdf").exists()
    assert (sample_dir / "photo.jpg").exists()

    # Created directories must be removed
    assert not (sample_dir / "Docs" / "Invoices").exists()
    assert not (sample_dir / "Docs").exists()
    assert not (sample_dir / "Media" / "Pics").exists()
    assert not (sample_dir / "Media").exists()


def test_undo_prevents_overwrite_if_original_path_occupied(sample_dir: Path, temp_manifest_dir: Path):
    """
    Safety Test:
    If a file has been moved, and then an external process creates a new file at the original path,
    undo must NOT overwrite the new file; it must fail safely and report collision.
    """
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    f1 = next(f for f in scan_result.files if f.filename == "notes.txt")
    suggestions = [
        FileSuggestion(file_id=f1.id, suggested_category="ArchivedNotes", suggested_filename="old_notes.txt")
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    exec_result = executor.execute_plan(plan)

    # Now create a new file at original location notes.txt
    (sample_dir / "notes.txt").write_text("New external content created after move")

    # Attempt rollback
    undo_engine = UndoEngine(manifest_dir=temp_manifest_dir)
    rollback_result = undo_engine.rollback(exec_result.undo_manifest_id)

    # Must fail or partially fail without overwriting the new file
    assert rollback_result.failed_count == 1
    assert "already occupied" in rollback_result.errors[0]
    assert (sample_dir / "notes.txt").read_text() == "New external content created after move"
    assert (sample_dir / "ArchivedNotes" / "old_notes.txt").exists()


def test_undo_handles_missing_target_file(sample_dir: Path, temp_manifest_dir: Path):
    """
    Safety Test:
    If a user externally deletes the moved file, undo records partial failure without crashing.
    """
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    f1 = next(f for f in scan_result.files if f.filename == "script.py")
    suggestions = [
        FileSuggestion(file_id=f1.id, suggested_category="Code", suggested_filename="script.py")
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    exec_result = executor.execute_plan(plan)

    # Externally delete the moved file
    (sample_dir / "Code" / "script.py").unlink()

    # Attempt rollback
    undo_engine = UndoEngine(manifest_dir=temp_manifest_dir)
    rollback_result = undo_engine.rollback(exec_result.undo_manifest_id)

    assert rollback_result.failed_count == 1
    assert "missing or moved externally" in rollback_result.errors[0]
    assert rollback_result.status == UndoStatus.ROLLBACK_FAILED


def test_undo_nonexistent_manifest_id(temp_manifest_dir: Path):
    """Verifies that requesting undo for an unknown manifest fails safely."""
    undo_engine = UndoEngine(manifest_dir=temp_manifest_dir)
    result = undo_engine.rollback("man_nonexistent_12345")
    assert result.status == UndoStatus.ROLLBACK_FAILED
    assert "not found" in result.errors[0]


def test_undo_already_rolled_back(sample_dir: Path, temp_manifest_dir: Path):
    """Verifies that attempting rollback twice is rejected as already rolled back."""
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(sample_dir)

    f1 = next(f for f in scan_result.files if f.filename == "photo.jpg")
    suggestions = [
        FileSuggestion(file_id=f1.id, suggested_category="Pics", suggested_filename="photo.jpg")
    ]

    planner = DeterministicOrganizationPlanner(sample_dir)
    plan = planner.create_preview_plan(scan_result.files, suggestions)

    executor = SafePlanExecutor(manifest_dir=temp_manifest_dir)
    exec_result = executor.execute_plan(plan)

    undo_engine = UndoEngine(manifest_dir=temp_manifest_dir)
    first_undo = undo_engine.rollback(exec_result.undo_manifest_id)
    assert first_undo.status == UndoStatus.ROLLED_BACK

    # Second undo
    second_undo = undo_engine.rollback(exec_result.undo_manifest_id)
    assert "already been rolled back" in second_undo.errors[0]


def test_undo_rejects_path_traversal_in_manifest(sample_dir: Path, temp_manifest_dir: Path, tmp_path: Path):
    """
    Security Test:
    Verifies that if a corrupted or hostile manifest specifies paths outside root,
    UndoEngine blocks the rollback and flags a security violation.
    """
    outside_file = tmp_path / "outside_secret.txt"
    outside_file.write_text("outside data")

    from backend.app.models.manifest import ExecutedStep, UndoManifest

    hostile_manifest = UndoManifest(
        manifest_id="man_hostile_test_123",
        plan_id="plan_hostile",
        root_path=str(sample_dir),
        steps=[
            ExecutedStep(
                step_id=1,
                op_id="op_hostile",
                file_id="f_hostile",
                source_abs_path="/etc/evil_target.txt",  # Escapes root!
                target_abs_path=str(outside_file),
                file_size_bytes=12,
                mtime=1700000000.0,
                created_directories=["/etc"],
            )
        ],
        status=UndoStatus.APPLIED,
    )

    undo_engine = UndoEngine(manifest_dir=temp_manifest_dir)
    result = undo_engine.rollback(hostile_manifest)

    assert result.status == UndoStatus.ROLLBACK_FAILED
    assert result.failed_count == 1
    assert "Security containment failure" in result.errors[0]
