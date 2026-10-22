"""Tests for validator, path confinement, and collision detection."""

from pathlib import Path
import pytest

from backend.app.engine.validator import (
    PlanValidator,
    assert_path_contained,
    sanitize_component,
    validate_filename,
    validate_rel_path,
)
from backend.app.models.operation import (
    ConflictType,
    FileOperation,
    OperationType,
    generate_operation_id,
)


def test_sanitize_component():
    """Tests component sanitization against illegal and reserved tokens."""
    assert sanitize_component("report:2026.pdf") == "report_2026.pdf"
    assert sanitize_component("file/with/slashes") == "file_with_slashes"
    assert sanitize_component("CON") == "item_CON"
    assert sanitize_component("   ") == "unnamed_item"
    assert sanitize_component("test..") == "test"


def test_validate_filename_rules():
    """Tests filename validation rules."""
    # Valid filenames
    assert validate_filename("clean_document.pdf")[0] is True
    assert validate_filename("2026-10-22_backup.tar.gz")[0] is True

    # Invalid filenames
    assert validate_filename("")[0] is False
    assert validate_filename("..")[0] is False
    assert validate_filename(".")[0] is False
    assert validate_filename("bad:name.txt")[0] is False
    assert validate_filename("bad/name.txt")[0] is False
    assert validate_filename("bad\\name.txt")[0] is False
    assert validate_filename("CON.txt")[0] is False
    assert validate_filename("NUL")[0] is False
    assert validate_filename("trailing_dot.")[0] is False
    assert validate_filename(" leading_space.txt")[0] is False


def test_validate_rel_path_traversal():
    """Tests that parent traversal ('..') and absolute paths are strictly rejected."""
    # Valid relative paths
    assert validate_rel_path("Documents/report.pdf")[0] is True
    assert validate_rel_path("Images/2026/photo.jpg")[0] is True
    assert validate_rel_path("root_file.txt")[0] is True

    # Traversal attempts
    assert validate_rel_path("../escaped.txt")[0] is False
    assert validate_rel_path("Documents/../../escaped.txt")[0] is False
    assert validate_rel_path("/absolute/path.txt")[0] is False
    assert validate_rel_path("C:/Windows/path.txt")[0] is False


def test_assert_path_contained(tmp_path: Path):
    """Tests runtime root confinement assertion."""
    root = tmp_path / "jail_root"
    root.mkdir()
    inside_file = root / "nested" / "file.txt"
    outside_file = tmp_path / "outside_file.txt"

    # Inside passes
    assert_path_contained(root, inside_file)

    # Outside raises ValueError
    with pytest.raises(ValueError, match="Security violation"):
        assert_path_contained(root, outside_file)


def test_plan_validator_intra_batch_collision(sample_dir: Path):
    """Verifies that multiple operations mapping to the same destination are flagged as collisions."""
    validator = PlanValidator(sample_dir)

    ops = [
        FileOperation(
            op_id=generate_operation_id(),
            file_id="f1",
            source_rel_path="invoice_2026.pdf",
            target_rel_path="Documents/summary.pdf",
            op_type=OperationType.MOVE,
        ),
        FileOperation(
            op_id=generate_operation_id(),
            file_id="f2",
            source_rel_path="notes.txt",
            target_rel_path="Documents/summary.pdf",
            op_type=OperationType.MOVE,
        ),
    ]

    validated = validator.validate_operations(ops)

    for op in validated:
        assert op.has_conflict is True
        conflict_types = [c.conflict_type for c in op.conflicts]
        assert ConflictType.INTRA_BATCH_COLLISION in conflict_types


def test_plan_validator_filesystem_collision(sample_dir: Path):
    """Verifies that moving a file to a target that already exists on disk is flagged as a collision."""
    validator = PlanValidator(sample_dir)

    # invoice_2026.pdf and notes.txt both exist on disk in sample_dir
    ops = [
        FileOperation(
            op_id=generate_operation_id(),
            file_id="f1",
            source_rel_path="invoice_2026.pdf",
            target_rel_path="notes.txt",  # notes.txt already exists on disk
            op_type=OperationType.RENAME,
        )
    ]

    validated = validator.validate_operations(ops)
    assert validated[0].has_conflict is True
    conflict_types = [c.conflict_type for c in validated[0].conflicts]
    assert ConflictType.FILESYSTEM_COLLISION in conflict_types


def test_validator_source_not_found(sample_dir: Path):
    """Verifies that missing source files are flagged with SOURCE_NOT_FOUND."""
    validator = PlanValidator(sample_dir)
    ops = [
        FileOperation(
            op_id=generate_operation_id(),
            file_id="f_ghost",
            source_rel_path="ghost_file.txt",
            target_rel_path="Docs/ghost_file.txt",
        )
    ]
    validated = validator.validate_operations(ops)
    assert validated[0].has_conflict is True
    conflict_types = [c.conflict_type for c in validated[0].conflicts]
    assert ConflictType.SOURCE_NOT_FOUND in conflict_types


def test_validator_self_mapping_keep(sample_dir: Path):
    """Verifies that KEEP operations (source == target) do not trigger collisions."""
    validator = PlanValidator(sample_dir)
    ops = [
        FileOperation(
            op_id=generate_operation_id(),
            file_id="f_keep",
            source_rel_path="notes.txt",
            target_rel_path="notes.txt",
            op_type=OperationType.KEEP,
        )
    ]
    validated = validator.validate_operations(ops)
    assert validated[0].has_conflict is False


def test_validator_symlink_rejection(dir_with_symlink: Path):
    """Verifies that operations targeting or sourcing symlinks are rejected."""
    validator = PlanValidator(dir_with_symlink)
    ops = [
        FileOperation(
            op_id=generate_operation_id(),
            file_id="f_sym",
            source_rel_path="link_to_real.txt",
            target_rel_path="Moved/link_to_real.txt",
        )
    ]
    validated = validator.validate_operations(ops)
    assert validated[0].has_conflict is True
    conflict_types = [c.conflict_type for c in validated[0].conflicts]
    assert ConflictType.SYMLINK_REJECTED in conflict_types
