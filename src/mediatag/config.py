from __future__ import annotations

import os
import sys
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class TMDbCredentials:
    bearer_token: str | None = None
    api_key: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.bearer_token or self.api_key)


def load_tmdb_credentials() -> TMDbCredentials:
    """Load TMDb auth from .env or the process environment."""
    for env_path in _env_file_candidates():
        if env_path.exists():
            load_dotenv(env_path, override=False)
    load_dotenv(override=False)
    bearer_token = os.getenv("TMDB_BEARER_TOKEN", "").strip() or None
    api_key = os.getenv("TMDB_API_KEY", "").strip() or None
    return TMDbCredentials(bearer_token=bearer_token, api_key=api_key)


def load_tmdb_token() -> str | None:
    """Backward-compatible helper for callers that only support bearer auth."""
    return load_tmdb_credentials().bearer_token


def default_cover_dir() -> Path:
    if getattr(sys, "frozen", False):
        return app_support_dir() / "covers"
    return Path.cwd() / "covers"


def app_support_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Mediatag"
    if sys.platform == "win32":
        root = os.getenv("APPDATA")
        if root:
            return Path(root) / "Mediatag"
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "mediatag"


def _env_file_candidates() -> list[Path]:
    candidates = [
        Path.cwd() / ".env",
        app_support_dir() / ".env",
        Path.home() / ".mediatag" / ".env",
    ]

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        candidates.extend(
            [
                executable.parent / ".env",
                executable.parent.parent / "Resources" / ".env",
                executable.parent.parent.parent / ".env",
            ]
        )

    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        try:
            key = candidate.resolve()
        except FileNotFoundError:
            key = candidate
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique
