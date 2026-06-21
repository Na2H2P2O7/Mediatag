from __future__ import annotations

import platform
from pathlib import Path
from typing import Callable, Iterable

from .config import TMDbCredentials
from .media import apply_faststart, download_image, embed_mp4_cover, normalize_poster, save_cover
from .models import ProcessResult
from .parser import clean_filename_part, parse_movie_filename
from .tmdb import TMDbClient, TMDbError

ProgressCallback = Callable[[int, int, str, int | None], None]
LogCallback = Callable[[str], None]
CoverCallback = Callable[[Path], None]


def safe_target_path(directory: Path, stem: str) -> Path:
    clean = clean_filename_part(stem)
    candidate = directory / f"{clean}.mp4"
    index = 1
    while candidate.exists():
        candidate = directory / f"{clean} ({index}).mp4"
        index += 1
    return candidate


def process_files(
    files: Iterable[str | Path],
    tmdb_token: str | TMDbCredentials,
    cover_dir: str | Path,
    progress: ProgressCallback | None = None,
    log: LogCallback | None = None,
    cover: CoverCallback | None = None,
    run_faststart: bool = True,
) -> list[ProcessResult]:
    paths = [Path(file) for file in files]
    client = TMDbClient(tmdb_token)
    cover_dir = Path(cover_dir)
    results: list[ProcessResult] = []

    for index, path in enumerate(paths, start=1):
        _progress(progress, index - 1, len(paths), f"Processing {path.name}", 0)
        try:
            result = process_one(path, client, cover_dir, log, cover, run_faststart)
        except TMDbError as exc:
            result = ProcessResult(path, "error", str(exc))
        except Exception as exc:  # Keep batch processing alive.
            result = ProcessResult(path, "error", f"{path.name}: {exc}")
        results.append(result)
        _log(log, result.message)
        _progress(progress, index, len(paths), result.message, 100)

    return results


def process_one(
    path: Path,
    client: TMDbClient,
    cover_dir: Path,
    log: LogCallback | None = None,
    cover: CoverCallback | None = None,
    run_faststart: bool = True,
) -> ProcessResult:
    if not path.exists():
        return ProcessResult(path, "error", f"{path.name}: file not found")
    if path.suffix.lower() != ".mp4":
        return ProcessResult(path, "skipped", f"{path.name}: unsupported in v1 (MP4 only)")

    parsed = parse_movie_filename(path)
    _log(log, f"{path.name}: candidates={list(parsed.candidates)} year={parsed.year}")
    metadata = client.search_best(parsed)
    if metadata is None:
        return ProcessResult(path, "skipped", f"{path.name}: no confident TMDb match with poster")

    _log(log, f"{path.name}: matched TMDb #{metadata.tmdb_id} -> {metadata.display_title}")
    poster = normalize_poster(download_image(client.poster_url(metadata.poster_path)))
    cover_path = save_cover(poster, cover_dir, clean_filename_part(metadata.display_title))
    if cover:
        cover(cover_path)

    if not embed_mp4_cover(path, poster):
        return ProcessResult(path, "error", f"{path.name}: poster embed verification failed")
    _log(log, f"{path.name}: poster embedded")

    if run_faststart:
        ffmpeg = _default_ffmpeg()
        if apply_faststart(path, ffmpeg=ffmpeg):
            _log(log, f"{path.name}: faststart applied")
        else:
            _log(log, f"{path.name}: faststart skipped or ffmpeg unavailable")

    target = safe_target_path(path.parent, metadata.display_title)
    path.rename(target)
    return ProcessResult(
        path,
        "done",
        f"{path.name} -> {target.name}",
        new_path=target,
        cover_path=cover_path,
    )


def _default_ffmpeg() -> str:
    if platform.system() == "Darwin":
        for candidate in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
            if Path(candidate).exists():
                return candidate
    return "ffmpeg"


def _log(callback: LogCallback | None, message: str) -> None:
    if callback:
        callback(message)


def _progress(callback: ProgressCallback | None, current: int, total: int, message: str, pct: int | None) -> None:
    if callback:
        callback(current, total, message, pct)
