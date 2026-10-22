"""Tests for the SlothSort safe demo seed utility."""

from pathlib import Path
import pytest

from backend.app.cli.seed_demo import (
    DEMO_FILES,
    format_cleanup_command,
    main,
    seed_demo_directory,
    validate_destination,
)


def test_validate_destination_valid_tmp_dir(tmp_path: Path):
    target = tmp_path / "my_demo_folder"
    validated = validate_destination(str(target))
    assert validated == target.resolve()


def test_validate_destination_rejects_empty():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_destination("")
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_destination("   ")


def test_validate_destination_rejects_traversal(tmp_path: Path):
    malicious = str(tmp_path / "sub" / ".." / ".." / "etc")
    with pytest.raises(ValueError, match="Path traversal"):
        validate_destination(malicious)


def test_validate_destination_rejects_system_paths():
    with pytest.raises(ValueError, match="protected system directory"):
        validate_destination("/etc")
    with pytest.raises(ValueError, match="protected system"):
        validate_destination("/usr/bin")
    with pytest.raises(ValueError, match="protected system"):
        validate_destination("/")


def test_validate_destination_rejects_sensitive_user_dirs(tmp_path: Path):
    ssh_dir = tmp_path / ".ssh"
    with pytest.raises(ValueError, match="protected credential folder"):
        validate_destination(str(ssh_dir))


def test_validate_destination_rejects_symlink_dir(tmp_path: Path):
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    symlink_dir = tmp_path / "symlink_dir"
    symlink_dir.symlink_to(real_dir)

    with pytest.raises(ValueError, match="cannot be a symbolic link"):
        validate_destination(str(symlink_dir))


def test_seed_demo_directory_dry_run(tmp_path: Path):
    target = tmp_path / "dry_run_target"
    created, skipped = seed_demo_directory(target, dry_run=True)

    assert len(created) == len(DEMO_FILES)
    assert len(skipped) == 0
    # Directory should NOT have been created
    assert not target.exists()


def test_seed_demo_directory_actual_creation(tmp_path: Path):
    target = tmp_path / "actual_demo"
    created, skipped = seed_demo_directory(target, dry_run=False)

    assert len(created) == len(DEMO_FILES)
    assert len(skipped) == 0
    assert target.is_dir()

    # Verify all files exist and are contained strictly inside target
    for f in created:
        assert f.exists()
        assert f.is_file()
        assert f.resolve().is_relative_to(target.resolve())
        assert f.stat().st_size > 0


def test_seed_demo_collision_prevention_never_overwrites(tmp_path: Path):
    target = tmp_path / "collision_test"
    target.mkdir()

    # Pre-create one of the files with custom content
    existing_file = target / "invoice_2026_q3_draft.pdf"
    original_sentinel = "ORIGINAL_USER_CONTENT_DO_NOT_TOUCH"
    existing_file.write_text(original_sentinel, encoding="utf-8")

    # Run seed
    created, skipped = seed_demo_directory(target, dry_run=False)

    # invoice should be in skipped, NOT created
    assert any(f.name == "invoice_2026_q3_draft.pdf" for f, _ in skipped)
    assert not any(f.name == "invoice_2026_q3_draft.pdf" for f in created)

    # Content must remain 100% intact
    assert existing_file.read_text(encoding="utf-8") == original_sentinel


def test_seed_demo_rejects_path_escape(tmp_path: Path):
    target = tmp_path / "escape_test"
    target.mkdir()

    rogue_spec = [
        {
            "filename": "../outside.txt",
            "content": "illegal escape",
            "is_binary": False,
        }
    ]

    with pytest.raises(ValueError, match="escapes target"):
        seed_demo_directory(target, file_specs=rogue_spec)


def test_format_cleanup_command(tmp_path: Path):
    target = tmp_path / "cleanup_demo"
    sample_files = [target / "file1.txt", target / "file2.pdf"]
    cmd = format_cleanup_command(sample_files, target)
    assert "rm -f" in cmd
    assert "file1.txt" in cmd
    assert "file2.pdf" in cmd
    assert f'rm -rf "{target.resolve()}"' in cmd


def test_cli_main_execution(tmp_path: Path, capsys):
    target = tmp_path / "cli_demo"
    ret = main([str(target)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "SlothSort Demo Seed Utility [EXECUTING]" in captured.out
    assert "Created 12 harmless demo file(s)" in captured.out
    assert "Cleanup Instructions:" in captured.out
    assert (target / "invoice_2026_q3_draft.pdf").exists()


def test_cli_main_dry_run(tmp_path: Path, capsys):
    target = tmp_path / "cli_dry_run"
    ret = main(["--dry-run", str(target)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "[DRY-RUN PREVIEW]" in captured.out
    assert "Would create 12 harmless demo file(s)" in captured.out
    assert not target.exists()


def test_cli_main_invalid_path(capsys):
    ret = main(["/etc"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
