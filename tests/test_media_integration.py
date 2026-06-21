import shutil
import subprocess

import pytest
from PIL import Image

from mediatag.media import embed_mp4_cover, normalize_poster


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_embed_cover_into_synthetic_mp4(tmp_path):
    mp4 = tmp_path / "fixture.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:d=0.1",
            "-pix_fmt",
            "yuv420p",
            str(mp4),
        ],
        check=True,
    )

    poster = tmp_path / "poster.png"
    Image.new("RGB", (32, 48), color=(10, 80, 180)).save(poster)
    image_data = normalize_poster(poster.read_bytes())

    assert embed_mp4_cover(mp4, image_data)
