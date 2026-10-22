"""
Safe Demo Seed Utility for SlothSort.

Populates a user-selected target directory with realistic, harmless dummy files
(documents, code, media stubs, archives) to safely test and demonstrate SlothSort.

Guarantees:
1. Never writes outside the explicitly specified destination directory.
2. Never overwrites existing files (collision detection skips existing files).
3. Never uses real personal documents or user data.
4. Provides full dry-run preview (--dry-run).
5. Outputs created files and exact cleanup command.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Protected operating system and credential paths
FORBIDDEN_PATHS = {
    "/",
    "/bin",
    "/sbin",
    "/usr",
    "/usr/bin",
    "/usr/sbin",
    "/etc",
    "/sys",
    "/proc",
    "/dev",
    "/boot",
    "/root",
    "/run",
    "/var/run",
    "/var/log",
}

FORBIDDEN_USER_NAMES = {
    ".ssh",
    ".gnupg",
    ".aws",
    ".azure",
    ".kube",
    ".docker",
}

# 12 Harmless, realistic dummy files across multiple common file types
DEMO_FILES: List[Dict[str, Any]] = [
    {
        "filename": "invoice_2026_q3_draft.pdf",
        "category_hint": "Finance",
        "content": "%PDF-1.4\n% SlothSort Harmless Dummy PDF Invoice Q3 2026\n%%EOF\n",
        "is_binary": False,
    },
    {
        "filename": "q3_tax_receipt_office_supplies.pdf",
        "category_hint": "Finance",
        "content": "%PDF-1.4\n% SlothSort Harmless Dummy Tax Receipt Office Supplies\n%%EOF\n",
        "is_binary": False,
    },
    {
        "filename": "meeting_notes_hacktoberfest_launch.txt",
        "category_hint": "Notes",
        "content": (
            "SlothSort Planning Notes — Hacktoberfest 2026 Week 3\n"
            "Challenge: Slow and Steady (Local-first AI)\n"
            "Goal: Organize cluttered files with Gemma 3 1B on consumer laptops.\n"
        ),
        "is_binary": False,
    },
    {
        "filename": "quarterly_priorities_draft.txt",
        "category_hint": "Notes",
        "content": (
            "Q4 2026 Product Priorities:\n"
            "- Improve local model batching\n"
            "- Add Tauri desktop packaging\n"
            "- Keep all data on device\n"
        ),
        "is_binary": False,
    },
    {
        "filename": "backup_runner_nightly.py",
        "category_hint": "Development",
        "content": (
            "#!/usr/bin/env python3\n"
            "# Harmless sample automation script\n"
            "def run_nightly_backup():\n"
            "    print('SlothSort demo automation runner active.')\n\n"
            "if __name__ == '__main__':\n"
            "    run_nightly_backup()\n"
        ),
        "is_binary": False,
    },
    {
        "filename": "styles_forest_palette.css",
        "category_hint": "Development",
        "content": (
            "/* SlothSort Design Palette: Forest Green & Cream */\n"
            ":root {\n"
            "  --color-primary: #1b4332;\n"
            "  --color-accent: #52b788;\n"
            "  --color-bg: #faf9f6;\n"
            "}\n"
        ),
        "is_binary": False,
    },
    {
        "filename": "docker-compose.staging.yml",
        "category_hint": "Development",
        "content": (
            "version: '3.8'\n"
            "services:\n"
            "  demo-service:\n"
            "    image: alpine:3.20\n"
            "    command: ['echo', 'SlothSort harmless container config']\n"
        ),
        "is_binary": False,
    },
    {
        "filename": "sunset_beach_trip_2026.jpg",
        "category_hint": "Images",
        # Minimal harmless JPEG marker header
        "content": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00SlothSortDummyJPEG\xff\xd9",
        "is_binary": True,
    },
    {
        "filename": "screenshot_terminal_log_error.png",
        "category_hint": "Images",
        # Minimal 1x1 harmless PNG header
        "content": (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00"
            b"\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
        "is_binary": True,
    },
    {
        "filename": "client_assets_archive_2026.zip",
        "category_hint": "Archives",
        # Minimal empty zip record
        "content": b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        "is_binary": True,
    },
    {
        "filename": "raw_telemetry_dump_october.tar.gz",
        "category_hint": "Archives",
        # Minimal gzip empty stream
        "content": b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        "is_binary": True,
    },
    {
        "filename": "device_firmware_driver_v4.bin",
        "category_hint": "System",
        "content": b"SLOTHSORT_DUMMY_BENIGN_BINARY_DATA_FOR_DEMONSTRATION_ONLY\n",
        "is_binary": True,
    },
]


def validate_destination(target_path_str: str) -> Path:
    """
    Validates that the target path is a safe directory for demo seeding.
    Rejects path traversal, system-critical directories, credential directories,
    and symbolic links.
    """
    if not target_path_str or not target_path_str.strip():
        raise ValueError("Target directory path cannot be empty.")

    clean_str = target_path_str.strip()

    # Reject traversal tokens
    parts = clean_str.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError(f"Path traversal ('..') is strictly forbidden: '{clean_str}'")

    raw_path = Path(clean_str)

    # Check for symlink before resolving
    if raw_path.is_symlink():
        raise ValueError(f"Target directory cannot be a symbolic link: '{clean_str}'")

    # Canonicalize
    canonical = raw_path.resolve()
    canonical_str = str(canonical)

    # Check forbidden system paths
    if canonical_str in FORBIDDEN_PATHS:
        raise ValueError(f"Access denied: '{canonical_str}' is a protected system directory.")

    for forbidden in FORBIDDEN_PATHS:
        if forbidden != "/" and (canonical_str == forbidden or canonical_str.startswith(f"{forbidden}/")):
            raise ValueError(f"Access denied: '{canonical_str}' is inside protected system path '{forbidden}'.")

    # Check sensitive credential directory names
    for part in canonical.parts:
        if part in FORBIDDEN_USER_NAMES:
            raise ValueError(f"Access denied: path contains protected credential folder '{part}'.")

    return canonical


def seed_demo_directory(
    target_dir: Path,
    dry_run: bool = False,
    file_specs: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """
    Populates target_dir with sample dummy files.

    Returns:
        Tuple of:
            - list of created (or proposed if dry_run) Path objects
            - list of skipped (Path, reason) tuples
    """
    specs = file_specs if file_specs is not None else DEMO_FILES
    created: List[Path] = []
    skipped: List[Tuple[Path, str]] = []

    # If dry_run is false, ensure target directory exists
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    target_canonical = target_dir.resolve()

    for spec in specs:
        filename = spec["filename"]
        dest_file = target_dir / filename

        # Security check: Ensure dest_file resolves strictly inside target_canonical
        try:
            dest_canonical = dest_file.resolve()
            if not dest_canonical.is_relative_to(target_canonical):
                raise ValueError(
                    f"Security violation: File path '{dest_file}' escapes target '{target_canonical}'."
                )
        except AttributeError:
            # Fallback for Python < 3.9 if ever run
            if not str(dest_canonical).startswith(str(target_canonical)):
                raise ValueError("Path escapes destination directory.")

        # Overwrite prevention check
        if dest_file.exists():
            skipped.append((dest_file, "File already exists (overwrite prevented)"))
            continue

        if dry_run:
            created.append(dest_file)
        else:
            is_bin = spec.get("is_binary", False)
            content = spec["content"]
            if is_bin:
                dest_file.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
            else:
                dest_file.write_text(content if isinstance(content, str) else content.decode("utf-8"), encoding="utf-8")
            created.append(dest_file)

    return created, skipped


def format_cleanup_command(created_files: List[Path], target_dir: Path) -> str:
    """Returns a safe cleanup command to remove generated demo files."""
    if not created_files:
        return f"# No files created in {target_dir}"

    escaped_paths = " \\\n  ".join(f'"{p.resolve()}"' for p in created_files)
    return (
        f"# Run this command to remove only the generated demo files:\n"
        f"rm -f \\\n  {escaped_paths}\n\n"
        f"# Or remove the entire demo directory if it was created exclusively for testing:\n"
        f'rm -rf "{target_dir.resolve()}"'
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="slothsort-seed-demo",
        description="Populates a directory with realistic, harmless dummy files for testing SlothSort.",
    )
    parser.add_argument(
        "target",
        help="Path to the destination directory to seed with demo files (e.g., /tmp/slothsort_demo)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Simulate file creation without writing anything to disk.",
    )

    args = parser.parse_args(argv)

    try:
        target_path = validate_destination(args.target)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    mode_label = "[DRY-RUN PREVIEW]" if args.dry_run else "[EXECUTING]"
    print(f"🦥 SlothSort Demo Seed Utility {mode_label}")
    print(f"📁 Target Directory: {target_path}")
    print("-" * 60)

    try:
        created, skipped = seed_demo_directory(target_path, dry_run=args.dry_run)
    except Exception as e:
        print(f"❌ Error seeding directory: {e}", file=sys.stderr)
        return 1

    if created:
        action_word = "Would create" if args.dry_run else "Created"
        print(f"✨ {action_word} {len(created)} harmless demo file(s):")
        for f in created:
            print(f"   • {f.name}")
    else:
        print("ℹ️  No new files created.")

    if skipped:
        print(f"\n⚠️  Skipped {len(skipped)} existing file(s) to prevent overwrites:")
        for f, reason in skipped:
            print(f"   • {f.name} ({reason})")

    print("\n" + "=" * 60)
    print("🧹 Cleanup Instructions:")
    print(format_cleanup_command(created, target_path))
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
