"""Undo and history API router."""

from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.app.api.schemas import UndoRequest
from backend.app.config import settings
from backend.app.engine.manifest import ManifestStorage
from backend.app.engine.undo import UndoEngine
from backend.app.models.manifest import RollbackResult, UndoManifest
from backend.app.security import default_folder_policy

router = APIRouter(tags=["Undo & History"])


@router.post(
    "/undo",
    response_model=RollbackResult,
    summary="Roll back an executed batch",
    description="Restores files from a previous operation batch to their exact original locations and cleans up empty created folders.",
)
async def rollback_batch(req: UndoRequest) -> RollbackResult:
    storage = ManifestStorage(settings.MANIFEST_DIR)
    manifest = storage.load_manifest(req.manifest_id)

    if manifest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manifest with ID '{req.manifest_id}' was not found or is corrupted.",
        )

    # Verify that the manifest's root path is within authorized bounds
    default_folder_policy.validate_folder_path(manifest.root_path)

    undo_engine = UndoEngine(manifest_dir=settings.MANIFEST_DIR)
    return undo_engine.rollback(manifest)


@router.get(
    "/history",
    response_model=List[UndoManifest],
    summary="List operation history manifests",
    description="Retrieves a list of previous operation manifests and their current rollback statuses, newest first.",
)
async def list_history() -> List[UndoManifest]:
    storage = ManifestStorage(settings.MANIFEST_DIR)
    return storage.list_manifests()
