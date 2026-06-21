from __future__ import annotations

import os
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
    load_dotenv()
    bearer_token = os.getenv("TMDB_BEARER_TOKEN", "").strip() or None
    api_key = os.getenv("TMDB_API_KEY", "").strip() or None
    return TMDbCredentials(bearer_token=bearer_token, api_key=api_key)


def load_tmdb_token() -> str | None:
    """Backward-compatible helper for callers that only support bearer auth."""
    return load_tmdb_credentials().bearer_token


def default_cover_dir() -> Path:
    return Path.cwd() / "covers"
