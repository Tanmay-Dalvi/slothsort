"""Pytest fixtures for SlothSort test suite."""

import os
from pathlib import Path
import pytest
from typing import Generator

from backend.app.models.file import FileMetadata, generate_file_id


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Fixture providing an empty temporary directory."""
    d = tmp_path / "empty_folder"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """
    Fixture providing a populated test folder with mixed files:
    - invoice_2026.pdf (120 bytes)
    - photo.jpg (250 bytes)
    - notes.txt (50 bytes)
    - script.py (80 bytes)
    - archive.zip (300 bytes)
    - subfolder/nested_doc.docx (90 bytes)
    """
    root = tmp_path / "messy_folder"
    root.mkdir(parents=True, exist_ok=True)

    (root / "invoice_2026.pdf").write_bytes(b"PDF-1.4 header content " * 5)
    (root / "photo.jpg").write_bytes(b"JPEG binary data " * 15)
    (root / "notes.txt").write_bytes(b"Quick notes on testing\n" * 2)
    (root / "script.py").write_bytes(b"print('hello world')\n" * 4)
    (root / "archive.zip").write_bytes(b"PK\x03\x04 fake zip binary data" * 10)

    sub = root / "subfolder"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "nested_doc.docx").write_bytes(b"Word document content " * 4)

    return root


@pytest.fixture
def dir_with_symlink(tmp_path: Path) -> Path:
    """Fixture providing a folder containing symbolic links."""
    root = tmp_path / "symlink_folder"
    root.mkdir(parents=True, exist_ok=True)

    # Real file
    real_file = root / "real_file.txt"
    real_file.write_text("Real content")

    # Internal symlink to file
    symlink_file = root / "link_to_real.txt"
    try:
        symlink_file.symlink_to(real_file)
    except OSError:
        pass

    # External file outside root
    external_dir = tmp_path / "external_outside"
    external_dir.mkdir(parents=True, exist_ok=True)
    ext_file = external_dir / "external_secret.txt"
    ext_file.write_text("Secret outside root")

    # Symlink pointing outside root
    ext_symlink = root / "link_outside.txt"
    try:
        ext_symlink.symlink_to(ext_file)
    except OSError:
        pass

    # Symlink directory
    ext_symlink_dir = root / "link_dir_outside"
    try:
        ext_symlink_dir.symlink_to(external_dir)
    except OSError:
        pass

    return root


@pytest.fixture
def temp_manifest_dir(tmp_path: Path) -> Path:
    """Fixture providing an isolated manifest storage directory."""
    d = tmp_path / "test_manifests"
    d.mkdir(parents=True, exist_ok=True)
    return d
