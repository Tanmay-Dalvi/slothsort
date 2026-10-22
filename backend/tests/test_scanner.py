"""Tests for SafeFolderScanner."""

import os
from pathlib import Path
import pytest

from backend.app.engine.scanner import SafeFolderScanner


def test_scanner_normal_folder(sample_dir: Path):
    """Verifies that normal files are scanned with accurate metadata."""
    scanner = SafeFolderScanner()
    result = scanner.scan(sample_dir)

    assert result.total_files == 6
    assert result.total_bytes > 0
    assert len(result.files) == 6
    assert len(result.errors) == 0

    filenames = {f.filename for f in result.files}
    assert "invoice_2026.pdf" in filenames
    assert "photo.jpg" in filenames
    assert "notes.txt" in filenames
    assert "script.py" in filenames
    assert "archive.zip" in filenames
    assert "nested_doc.docx" in filenames

    # Check extension normalization and metadata
    pdf_meta = next(f for f in result.files if f.filename == "invoice_2026.pdf")
    assert pdf_meta.extension == "pdf"
    assert pdf_meta.size_bytes == (sample_dir / "invoice_2026.pdf").stat().st_size
    assert pdf_meta.is_symlink is False
    assert pdf_meta.is_accessible is True
    assert pdf_meta.id is not None


def test_scanner_empty_folder(empty_dir: Path):
    """Verifies scanning an empty folder returns zero counts without error."""
    scanner = SafeFolderScanner()
    result = scanner.scan(empty_dir)

    assert result.total_files == 0
    assert result.total_bytes == 0
    assert len(result.files) == 0
    assert len(result.skipped_files) == 0
    assert len(result.errors) == 0


def test_scanner_skips_symlinks(dir_with_symlink: Path):
    """Verifies that symlinks (file and directory) are never followed and are recorded as skipped."""
    scanner = SafeFolderScanner()
    result = scanner.scan(dir_with_symlink)

    # Only the 1 real file should be in files
    assert result.total_files == 1
    assert result.files[0].filename == "real_file.txt"

    # Symlinks should be recorded in skipped_files
    skipped_reasons = [s.reason for s in result.skipped_files]
    assert any("Symbolic link" in r for r in skipped_reasons)


def test_scanner_ignores_system_directories(sample_dir: Path):
    """Verifies that system/build directories like .git and node_modules are pruned and skipped."""
    git_dir = sample_dir / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    (git_dir / "config").write_text("git config dummy")

    node_modules = sample_dir / "node_modules"
    node_modules.mkdir(parents=True, exist_ok=True)
    (node_modules / "pkg.json").write_text("{}")

    scanner = SafeFolderScanner()
    result = scanner.scan(sample_dir)

    # Files inside .git and node_modules must NOT be included in files
    filenames = {f.filename for f in result.files}
    assert "config" not in filenames
    assert "pkg.json" not in filenames

    # Should be recorded in skipped_files
    skipped_paths = [s.path for s in result.skipped_files]
    assert ".git" in skipped_paths
    assert "node_modules" in skipped_paths


def test_scanner_invalid_path():
    """Verifies that non-existent directory raises ValueError."""
    scanner = SafeFolderScanner()
    with pytest.raises(ValueError, match="does not exist"):
        scanner.scan(Path("/nonexistent/path/for/slothsort/test"))


def test_scanner_max_depth(tmp_path: Path):
    """Verifies that scanning respects max_depth boundary."""
    deep_root = tmp_path / "deep_root"
    deep_root.mkdir()
    (deep_root / "level0.txt").write_text("0")

    level1 = deep_root / "l1"
    level1.mkdir()
    (level1 / "level1.txt").write_text("1")

    level2 = level1 / "l2"
    level2.mkdir()
    (level2 / "level2.txt").write_text("2")

    # Max depth 1 means only root level (depth 0 relative to root)
    scanner = SafeFolderScanner(max_depth=1)
    result = scanner.scan(deep_root)

    scanned_names = {f.filename for f in result.files}
    assert "level0.txt" in scanned_names
    assert "level2.txt" not in scanned_names


def test_scanner_inaccessible_directory(tmp_path: Path):
    """Verifies that unreadable directory does not crash scan and is recorded."""
    root = tmp_path / "inaccessible_root"
    root.mkdir()
    (root / "readable.txt").write_text("hello")

    locked_dir = root / "locked"
    locked_dir.mkdir()
    (locked_dir / "secret.txt").write_text("secret")

    try:
        locked_dir.chmod(0o000)
        scanner = SafeFolderScanner()
        result = scanner.scan(root)

        # Scans readable files
        assert any(f.filename == "readable.txt" for f in result.files)
    finally:
        locked_dir.chmod(0o755)
