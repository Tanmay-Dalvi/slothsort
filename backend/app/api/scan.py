"""Folder scanning API router."""

from fastapi import APIRouter, HTTPException, status

from backend.app.api.schemas import ScanRequest
from backend.app.engine.scanner import SafeFolderScanner
from backend.app.models.file import ScanResult
from backend.app.security import default_folder_policy

router = APIRouter(tags=["Scanning"])


@router.post(
    "/scan",
    response_model=ScanResult,
    summary="Scan user-selected folder",
    description="Scans an authorized folder, extracts metadata safely without reading file contents, and returns a ScanResult.",
)
async def scan_folder(req: ScanRequest) -> ScanResult:
    # 1. Enforce folder-access authorization policy
    validated_root = default_folder_policy.validate_folder_path(req.folder_path)

    # 2. Run memory-efficient scanner
    scanner = SafeFolderScanner(max_depth=req.max_depth)
    try:
        return scanner.scan(validated_root)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filesystem scan error: {str(e)}",
        )
