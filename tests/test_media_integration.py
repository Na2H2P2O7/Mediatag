import io
import shutil
import subprocess

import pytest
from PIL import Image

from mediatag.media import embed_mp4_cover, normalize_poster, remove_mp4_cover


def test_normalize_poster_resizes_to_legacy_cover_height(tmp_path):
    poster = tmp_path / "large-poster.png"
    Image.new("RGB", (2000, 3000), color=(10, 80, 180)).save(poster)

    image_data = normalize_poster(poster.read_bytes())

    with Image.open(io.BytesIO(image_data)) as normalized:
        assert normalized.size == (359, 538)


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
    assert remove_mp4_cover(mp4)
