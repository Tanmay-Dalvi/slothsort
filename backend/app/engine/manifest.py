"""Persistence for undo manifests and transaction logs."""

import json
from pathlib import Path
from typing import List, Optional

from backend.app.config import settings
from backend.app.models.manifest import UndoManifest


class ManifestStorage:
    """Manages saving, loading, and listing undo manifests."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = (
            storage_dir if storage_dir is not None else settings.MANIFEST_DIR
        ).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _manifest_file(self, manifest_id: str) -> Path:
        safe_id = "".join(c for c in manifest_id if c.isalnum() or c in "_-")
        return self.storage_dir / f"{safe_id}.json"

    def save_manifest(self, manifest: UndoManifest) -> Path:
        """Saves a manifest as formatted JSON."""
        file_path = self._manifest_file(manifest.manifest_id)
        data = manifest.model_dump()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path

    def load_manifest(self, manifest_id: str) -> Optional[UndoManifest]:
        """Loads a manifest by ID, or None if not found or corrupted."""
        file_path = self._manifest_file(manifest_id)
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UndoManifest.model_validate(data)
        except Exception:
            return None

    def list_manifests(self) -> List[UndoManifest]:
        """Lists all stored manifests sorted newest first."""
        manifests: List[UndoManifest] = []
        for p in self.storage_dir.glob("man_*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    manifests.append(UndoManifest.model_validate(json.load(f)))
            except Exception:
                continue
        manifests.sort(key=lambda m: m.executed_at, reverse=True)
        return manifests
