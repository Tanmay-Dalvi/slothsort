"""Integration tests for SlothSort REST API routes and security guardrails."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from backend.app.models.operation import ConflictType, FileOperation, OperationType
from backend.app.services.plan_store import plan_store


@pytest.fixture(autouse=True)
def clear_plan_store():
    """Ensure in-memory plan store is reset before each test."""
    plan_store.clear()
    yield
    plan_store.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ==============================================================================
# 1. Folder Scanning Tests (POST /api/scan)
# ==============================================================================

def test_api_scan_valid_folder(client: TestClient, sample_dir: Path):
    """Verifies scanning a valid authorized directory returns 200 OK and ScanResult."""
    response = client.post("/api/scan", json={"folder_path": str(sample_dir)})
    assert response.status_code == 200

    data = response.json()
    assert data["root_path"] == str(sample_dir.resolve())
    assert data["total_files"] == 6
    assert data["total_bytes"] > 0
    assert len(data["files"]) == 6
    assert len(data["errors"]) == 0

    filenames = {f["filename"] for f in data["files"]}
    assert "invoice_2026.pdf" in filenames


def test_api_scan_empty_folder(client: TestClient, empty_dir: Path):
    """Verifies scanning an empty directory returns 200 OK with total_files=0."""
    response = client.post("/api/scan", json={"folder_path": str(empty_dir)})
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 0
    assert len(data["files"]) == 0


def test_api_scan_nonexistent_folder(client: TestClient):
    """Verifies scanning a non-existent path returns 404 Not Found."""
    response = client.post(
        "/api/scan", json={"folder_path": "/tmp/nonexistent_slothsort_folder_xyz123"}
    )
    assert response.status_code == 404
    assert "Target directory does not exist" in response.json()["detail"]


def test_api_scan_relative_path(client: TestClient):
    """Security Test: Verifies that relative paths are rejected with 400 Bad Request."""
    response = client.post("/api/scan", json={"folder_path": "relative/path/folder"})
    assert response.status_code == 400
    assert "must be an absolute path" in response.json()["detail"]


def test_api_scan_traversal_attack(client: TestClient):
    """Security Test: Verifies that directory traversal tokens ('..') are rejected."""
    response = client.post("/api/scan", json={"folder_path": "/tmp/../etc"})
    assert response.status_code == 400
    assert "traversal tokens" in response.json()["detail"]


def test_api_scan_unauthorized_system_path(client: TestClient):
    """Security Test: Verifies that system directories like /etc are blocked with 403 Forbidden."""
    response = client.post("/api/scan", json={"folder_path": "/etc"})
    assert response.status_code == 403
    assert "protected system" in response.json()["detail"]


def test_api_scan_symlink_root(client: TestClient, tmp_path: Path):
    """Security Test: Verifies that root directory cannot be a symbolic link."""
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    sym_dir = tmp_path / "sym_dir"
    try:
        sym_dir.symlink_to(real_dir)
        response = client.post("/api/scan", json={"folder_path": str(sym_dir)})
        assert response.status_code == 400
        assert "symbolic link" in response.json()["detail"]
    except OSError:
        pass


def test_api_scan_does_not_modify_disk(client: TestClient, sample_dir: Path):
    """Safety Test: Scanning a folder must be strictly read-only."""
    before_state = {p.name: p.stat().st_mtime for p in sample_dir.rglob("*") if p.is_file()}

    client.post("/api/scan", json={"folder_path": str(sample_dir)})

    after_state = {p.name: p.stat().st_mtime for p in sample_dir.rglob("*") if p.is_file()}
    assert before_state == after_state


# ==============================================================================
# 2. Provider Endpoint Tests (GET /api/providers)
# ==============================================================================

def test_api_get_providers(client: TestClient):
    """Verifies provider listing, health checks, and privacy disclosures."""
    response = client.get("/api/providers")
    assert response.status_code == 200

    providers = response.json()
    assert len(providers) >= 3

    provider_map = {p["provider_name"]: p for p in providers}
    assert "Deterministic Mock Provider" in provider_map
    assert "Local Ollama" in provider_map
    assert "Google Gemini" in provider_map

    # Disclosures
    assert "Local" in provider_map["Deterministic Mock Provider"]["privacy_notice"]
    assert "Cloud API" in provider_map["Google Gemini"]["privacy_notice"]


# ==============================================================================
# 3. Plan Generation Tests (POST /api/plan/generate)
# ==============================================================================

def test_api_plan_generate_mock(client: TestClient, sample_dir: Path):
    """Verifies generating an organization plan with the mock provider."""
    response = client.post(
        "/api/plan/generate",
        json={
            "folder_path": str(sample_dir),
            "provider_id": "mock",
            "options": {"naming_convention": "preserve"},
        },
    )
    assert response.status_code == 200
    plan = response.json()

    assert plan["plan_id"].startswith("plan_")
    assert plan["root_path"] == str(sample_dir.resolve())
    assert plan["provider_used"] == "mock"
    assert plan["total_files"] == 6
    assert plan["is_validated"] is True
    assert plan["requires_approval"] is True
    assert len(plan["operations"]) == 6

    # Verify preview-only: No files moved or created on disk
    assert not (sample_dir / "Documents").exists()
    assert (sample_dir / "invoice_2026.pdf").exists()


def test_api_plan_generate_empty_folder(client: TestClient, empty_dir: Path):
    """Verifies generating a plan for an empty directory returns an empty plan without errors."""
    response = client.post(
        "/api/plan/generate",
        json={"folder_path": str(empty_dir), "provider_id": "mock"},
    )
    assert response.status_code == 200
    plan = response.json()
    assert plan["total_files"] == 0
    assert len(plan["operations"]) == 0


def test_api_plan_generate_unauthorized_folder(client: TestClient):
    """Security Test: Generating a plan for unauthorized path returns 403 Forbidden."""
    response = client.post(
        "/api/plan/generate",
        json={"folder_path": "/etc", "provider_id": "mock"},
    )
    assert response.status_code == 403


def test_api_plan_generate_invalid_provider(client: TestClient, sample_dir: Path):
    """Verifies requesting an unknown provider returns 502 with error detail."""
    response = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "unknown_ai"},
    )
    assert response.status_code == 502
    assert "Unknown AI provider" in response.json()["detail"]


# ==============================================================================
# 4. Plan Validation Tests (POST /api/plan/validate)
# ==============================================================================

def test_api_plan_validate_edited_operations(client: TestClient, sample_dir: Path):
    """Verifies re-validating a user-edited plan detects destination collisions."""
    # 1. Generate plan
    gen_res = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "mock"},
    )
    plan = gen_res.json()
    plan_id = plan["plan_id"]
    operations = plan["operations"]

    # 2. Modify operations to force a duplicate destination collision
    operations[0]["target_rel_path"] = "Collisions/same.txt"
    operations[1]["target_rel_path"] = "Collisions/same.txt"

    val_res = client.post(
        "/api/plan/validate",
        json={"plan_id": plan_id, "operations": operations},
    )
    assert val_res.status_code == 200
    updated_plan = val_res.json()

    assert updated_plan["conflicts_detected"] > 0
    op0 = updated_plan["operations"][0]
    conflict_types = [c["conflict_type"] for c in op0["conflicts"]]
    assert ConflictType.INTRA_BATCH_COLLISION.value in conflict_types


def test_api_plan_validate_nonexistent_plan(client: TestClient):
    """Verifies that validating an unknown plan returns 404 Not Found."""
    response = client.post(
        "/api/plan/validate",
        json={"plan_id": "plan_nonexistent_999", "operations": []},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ==============================================================================
# 5. Plan Execution Tests (POST /api/plan/execute)
# ==============================================================================

def test_api_plan_execute_successful_and_undo(
    client: TestClient, sample_dir: Path, monkeypatch
):
    """
    End-to-End Test:
    1. Generate plan
    2. Execute approved operations
    3. Verify filesystem changes and undo manifest
    4. Call /api/undo and verify 100% restoration
    """
    # 1. Generate plan
    gen_res = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "mock"},
    )
    plan = gen_res.json()
    plan_id = plan["plan_id"]

    # Approve only first 2 operations
    approved_ids = [plan["operations"][0]["op_id"], plan["operations"][1]["op_id"]]

    # 2. Execute plan
    exec_res = client.post(
        "/api/plan/execute",
        json={"plan_id": plan_id, "approved_op_ids": approved_ids},
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()

    assert exec_data["status"] == "SUCCESS"
    assert exec_data["executed_count"] == 2
    assert exec_data["undo_manifest_id"] is not None
    manifest_id = exec_data["undo_manifest_id"]

    # 3. Check anti-replay: Re-executing same plan must fail with 409 Conflict
    re_exec_res = client.post(
        "/api/plan/execute",
        json={"plan_id": plan_id, "approved_op_ids": approved_ids},
    )
    assert re_exec_res.status_code == 409
    assert "already been executed" in re_exec_res.json()["detail"]

    # 4. Roll back via /api/undo
    undo_res = client.post("/api/undo", json={"manifest_id": manifest_id})
    assert undo_res.status_code == 200
    undo_data = undo_res.json()

    assert undo_data["status"] == "ROLLED_BACK"
    assert undo_data["restored_count"] == 2
    assert undo_data["failed_count"] == 0

    # Verify original files are back
    assert (sample_dir / "invoice_2026.pdf").exists()
    assert (sample_dir / "photo.jpg").exists()


def test_plan_replay_protection_persists_across_restart(
    client: TestClient, sample_dir: Path
):
    """
    Security Test:
    Even after simulated backend process restart (in-memory plan store wiped),
    an executed plan_id is recognized from persisted manifests on disk and blocked.
    """
    gen_res = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "mock"},
    )
    plan = gen_res.json()
    plan_id = plan["plan_id"]
    approved_ids = [plan["operations"][0]["op_id"]]

    # Execute plan
    exec_res = client.post(
        "/api/plan/execute",
        json={"plan_id": plan_id, "approved_op_ids": approved_ids},
    )
    assert exec_res.status_code == 200

    # Simulate server restart by clearing in-memory store and re-registering plan object
    # but with executed status remembered via manifest on disk
    orig_plan_obj = plan_store.get_plan(plan_id)
    plan_store._plans.clear()
    plan_store._executed_plan_ids.clear()

    # Re-inject plan object to simulate cached/stale plan resurrection attempt
    if orig_plan_obj:
        plan_store._plans[plan_id] = orig_plan_obj

    # Attempt replay execution
    replay_res = client.post(
        "/api/plan/execute",
        json={"plan_id": plan_id, "approved_op_ids": approved_ids},
    )
    assert replay_res.status_code == 409
    assert "already been executed" in replay_res.json()["detail"]



def test_api_plan_execute_invalid_operation_id(client: TestClient, sample_dir: Path):
    """Security Test: Passing an operation ID not belonging to the plan returns 400 Bad Request."""
    gen_res = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "mock"},
    )
    plan = gen_res.json()

    exec_res = client.post(
        "/api/plan/execute",
        json={"plan_id": plan["plan_id"], "approved_op_ids": ["op_forged_unknown"]},
    )
    assert exec_res.status_code == 400
    assert "does not belong to plan" in exec_res.json()["detail"]


# ==============================================================================
# 6. Undo & History Tests (POST /api/undo, GET /api/history)
# ==============================================================================

def test_api_undo_missing_manifest(client: TestClient):
    """Verifies that rolling back an unknown manifest returns 404 Not Found."""
    response = client.post("/api/undo", json={"manifest_id": "man_nonexistent_999"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_api_history_retrieval(client: TestClient, sample_dir: Path):
    """Verifies that executed batches are listed in /api/history."""
    # Generate and execute a 1-file plan
    gen_res = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "mock"},
    )
    plan = gen_res.json()
    op_id = plan["operations"][0]["op_id"]

    exec_res = client.post(
        "/api/plan/execute",
        json={"plan_id": plan["plan_id"], "approved_op_ids": [op_id]},
    )
    manifest_id = exec_res.json()["undo_manifest_id"]

    history_res = client.get("/api/history")
    assert history_res.status_code == 200
    manifests = history_res.json()

    assert any(m["manifest_id"] == manifest_id for m in manifests)


def test_api_history_handles_corrupted_manifest(client: TestClient, tmp_path: Path):
    """Safety Test: Corrupted JSON manifest files in storage do not crash /api/history."""
    corrupt_file = settings.MANIFEST_DIR / "man_corrupted_test.json"
    try:
        corrupt_file.write_text("BROKEN JSON { [")
        response = client.get("/api/history")
        assert response.status_code == 200
        # Corrupt file is safely ignored
        manifest_ids = [m["manifest_id"] for m in response.json()]
        assert "man_corrupted_test" not in manifest_ids
    finally:
        if corrupt_file.exists():
            corrupt_file.unlink()


# ==============================================================================
# 7. Privacy & Confidentiality Guarantee
# ==============================================================================

def test_responses_contain_zero_file_content_or_secrets(
    client: TestClient, sample_dir: Path
):
    """
    Privacy Audit Test:
    Ensures that file contents (e.g. text from notes.txt or fake binary from archive.zip)
    and internal secrets/API keys never leak in any API response payloads.
    """
    # 1. Scan response
    scan_res = client.post("/api/scan", json={"folder_path": str(sample_dir)})
    scan_text = scan_res.text
    assert "Quick notes on testing" not in scan_text
    assert "PK\x03\x04 fake zip" not in scan_text

    # 2. Plan response
    plan_res = client.post(
        "/api/plan/generate",
        json={"folder_path": str(sample_dir), "provider_id": "mock"},
    )
    plan_text = plan_res.text
    assert "Quick notes on testing" not in plan_text
    assert "PK\x03\x04 fake zip" not in plan_text

    # 3. Providers response
    providers_res = client.get("/api/providers")
    providers_text = providers_res.text
    assert "AIzaSy" not in providers_text
    assert "api_key" not in providers_text.lower() or "not configured" in providers_text.lower()
