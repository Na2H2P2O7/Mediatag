from __future__ import annotations

import io
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image

POSTER_TARGET_HEIGHT = 538


def download_image(url: str, timeout: int = 30) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def normalize_poster(image_data: bytes) -> bytes:
    with Image.open(io.BytesIO(image_data)) as img:
        img = img.convert("RGB")
        width, height = img.size
        if height != POSTER_TARGET_HEIGHT:
            target_width = max(1, round(width * POSTER_TARGET_HEIGHT / height))
            img = img.resize((target_width, POSTER_TARGET_HEIGHT), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=94, optimize=True)
        return output.getvalue()


def save_cover(image_data: bytes, cover_dir: Path, filename_stem: str) -> Path:
    cover_dir.mkdir(parents=True, exist_ok=True)
    path = cover_dir / f"{filename_stem}.jpg"
    path.write_bytes(image_data)
    return path


def embed_mp4_cover(mp4_path: Path, image_data: bytes) -> bool:
    video = MP4(mp4_path)
    video["covr"] = [MP4Cover(image_data, imageformat=MP4Cover.FORMAT_JPEG)]
    video.save()

    verify = MP4(mp4_path)
    return "covr" in verify and bool(verify["covr"])


def remove_mp4_cover(mp4_path: Path) -> bool:
    video = MP4(mp4_path)
    if "covr" not in video:
        return False
    del video["covr"]
    video.save()

    verify = MP4(mp4_path)
    return "covr" not in verify


def apply_faststart(mp4_path: Path, ffmpeg: str = "ffmpeg") -> bool:
    temp_path = mp4_path.with_suffix(mp4_path.suffix + ".faststart.tmp.mp4")
    backup_path = mp4_path.with_suffix(mp4_path.suffix + ".bak")
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(mp4_path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(temp_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or not temp_path.exists() or temp_path.stat().st_size == 0:
            if temp_path.exists():
                temp_path.unlink()
            return False

        for attempt in range(5):
            try:
                if backup_path.exists():
                    backup_path.unlink()
                os.replace(mp4_path, backup_path)
                os.replace(temp_path, mp4_path)
                backup_path.unlink(missing_ok=True)
                return True
            except PermissionError:
                time.sleep((attempt + 1) * 1.5)
                if backup_path.exists() and not mp4_path.exists():
                    shutil.move(str(backup_path), str(mp4_path))
        return False
    except FileNotFoundError:
        return False
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
