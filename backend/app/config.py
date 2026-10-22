"""Application configuration."""

import os
from pathlib import Path
from typing import Set


def _load_env_file() -> None:
    """Safely loads key-value pairs from a local .env file into os.environ."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and val:
                            os.environ[key] = val
                break
            except Exception:
                pass


_load_env_file()


class Settings:
    """SlothSort configuration parameters."""
    PROJECT_NAME: str = "SlothSort"
    VERSION: str = "0.1.0"

    # AI Configuration
    DEFAULT_PROVIDER: str = os.getenv("SLOTHSORT_DEFAULT_PROVIDER", "ollama")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:1b")

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def GEMINI_API_KEY(self) -> str:
        _load_env_file()
        return os.getenv("GEMINI_API_KEY", "")

    # Storage Paths
    USER_CONFIG_DIR: Path = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "slothsort"
    MANIFEST_DIR: Path = USER_CONFIG_DIR / "manifests"

    # Folder Access Security
    # Comma-separated list of allowed root directories (defaults to user home and /tmp)
    @property
    def ALLOWED_ROOTS(self) -> str:
        raw = os.getenv("SLOTHSORT_ALLOWED_ROOTS", "").strip()
        return raw if raw else f"{Path.home()},{Path('/tmp')}"

    @property
    def allowed_root_dirs(self) -> list[Path]:
        raw = self.ALLOWED_ROOTS
        return [Path(p.strip()).resolve() for p in raw.split(",") if p.strip()]

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

    # CORS Configuration
    @property
    def CORS_ORIGINS(self) -> list[str]:
        default_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        raw = os.getenv("SLOTHSORT_CORS_ORIGINS", "").strip()
        if not raw:
            return default_origins
        extras = [o.strip() for o in raw.split(",") if o.strip()]
        return list(dict.fromkeys(default_origins + extras))


settings = Settings()
