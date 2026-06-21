from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedMovieName:
    original_path: Path
    year: int | None
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class MovieMetadata:
    tmdb_id: int
    year: int
    chinese_title: str
    original_title: str
    display_title: str
    poster_path: str
    confidence: float


@dataclass(frozen=True)
class ProcessResult:
    path: Path
    status: str
    message: str
    new_path: Path | None = None
    cover_path: Path | None = None
