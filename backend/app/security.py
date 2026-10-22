"""Folder access security policy and path authorization guardrails."""

import os
from pathlib import Path
from typing import List, Optional, Set
from fastapi import HTTPException, status

from backend.app.config import settings

# Critical operating system directories that must NEVER be accessed or organized
FORBIDDEN_SYSTEM_PATHS: Set[str] = {
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

# Sensitive user credential directories that must never be targeted directly
SENSITIVE_USER_NAMES: Set[str] = {
    ".ssh",
    ".gnupg",
    ".aws",
    ".azure",
    ".kube",
    ".docker",
}


class FolderAccessPolicy:
    """
    Enforces folder-access authorization rules.

    Guarantees:
    1. Rejects relative paths and traversal attempts ('..', '//').
    2. Rejects system-critical directories (/etc, /sys, /proc, /dev, root /).
    3. Requires path to be strictly contained within authorized root directories (e.g. user home, /tmp).
    4. Rejects symbolic link root directories.
    5. Disallows targeting SlothSort's internal manifest repository.
    """

    def __init__(self, allowed_roots: Optional[List[Path]] = None):
        self.allowed_roots = (
            allowed_roots if allowed_roots is not None else settings.allowed_root_dirs
        )

    def validate_folder_path(self, raw_path: str) -> Path:
        """
        Validates and canonicalizes a user-provided directory path string.
        Returns the resolved Path if authorized, or raises HTTPException with appropriate status.
        """
        if not raw_path or not raw_path.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder path cannot be empty.",
            )

        # Disallow raw traversal patterns
        clean_raw = raw_path.strip()
        if ".." in clean_raw.split("/") or ".." in clean_raw.split("\\"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path traversal tokens ('..') are strictly prohibited in folder path.",
            )

        path_obj = Path(clean_raw)
        if not path_obj.is_absolute():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder path must be an absolute path.",
            )

        # Check symlink on the raw path before resolving
        if path_obj.is_symlink():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target root folder cannot be a symbolic link.",
            )

        if not path_obj.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target directory does not exist: '{clean_raw}'.",
            )

        if not path_obj.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target path is not a directory: '{clean_raw}'.",
            )

        canonical = path_obj.resolve()

        # Check forbidden system paths
        canonical_str = str(canonical)
        if canonical_str in FORBIDDEN_SYSTEM_PATHS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: '{canonical_str}' is a protected system directory.",
            )

        for forbidden in FORBIDDEN_SYSTEM_PATHS:
            if forbidden != "/" and (canonical_str == forbidden or canonical_str.startswith(f"{forbidden}/")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: '{canonical_str}' is inside protected system path '{forbidden}'.",
                )

        # Check sensitive user names
        for part in canonical.parts:
            if part in SENSITIVE_USER_NAMES:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: path contains protected sensitive credential folder '{part}'.",
                )

        # Prevent organizing SlothSort's own internal storage
        manifest_dir_canonical = settings.MANIFEST_DIR.resolve()
        if canonical == manifest_dir_canonical or canonical.is_relative_to(manifest_dir_canonical):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot organize SlothSort's internal manifest repository.",
            )

        # Confinement within configured authorized roots
        is_authorized = False
        for allowed_root in self.allowed_roots:
            try:
                resolved_allowed = allowed_root.resolve()
                if canonical.is_relative_to(resolved_allowed):
                    is_authorized = True
                    break
            except (ValueError, OSError):
                continue

        if not is_authorized:
            allowed_list = ", ".join(str(r) for r in self.allowed_roots)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Folder '{canonical_str}' is outside authorized root directories ({allowed_list}).",
            )

        return canonical


default_folder_policy = FolderAccessPolicy()
