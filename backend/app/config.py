"""Application configuration."""

import os
from pathlib import Path
from typing import Set


class Settings:
    """SlothSort configuration parameters."""
    PROJECT_NAME: str = "SlothSort"
    VERSION: str = "0.1.0"

    # AI Configuration
    DEFAULT_PROVIDER: str = os.getenv("SLOTHSORT_DEFAULT_PROVIDER", "ollama")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:1b")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Storage Paths
    USER_CONFIG_DIR: Path = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "slothsort"
    MANIFEST_DIR: Path = USER_CONFIG_DIR / "manifests"

    # Folder Access Security
    # Comma-separated list of allowed root directories (defaults to user home and /tmp)
    ALLOWED_ROOTS: str = os.getenv("SLOTHSORT_ALLOWED_ROOTS", f"{Path.home()},{Path('/tmp')}")

    @property
    def allowed_root_dirs(self) -> list[Path]:
        return [Path(p.strip()).resolve() for p in self.ALLOWED_ROOTS.split(",") if p.strip()]

    # Safety & Scanning Limits
    MAX_SCAN_DEPTH: int = 12
    MAX_BATCH_SIZE: int = 20
    IGNORED_DIR_NAMES: Set[str] = {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".slothsort",
        ".idea",
        ".vscode",
        ".pytest_cache",
    }


settings = Settings()
