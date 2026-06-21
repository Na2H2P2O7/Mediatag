from pathlib import Path

from mediatag.models import MovieMetadata
from mediatag.pipeline import process_one, safe_target_path


def test_safe_target_path_adds_collision_suffix(tmp_path):
    existing = tmp_path / "2025 火遮眼.mp4"
    existing.write_text("x")

    target = safe_target_path(tmp_path, "2025 火遮眼")

    assert target.name == "2025 火遮眼 (1).mp4"


def test_safe_target_path_keeps_current_normalized_file(tmp_path):
    current = tmp_path / "2025 火遮眼.mp4"
    current.write_text("x")

    target = safe_target_path(tmp_path, "2025 火遮眼", current_path=current)

    assert target == current


def test_process_one_skips_unsupported_extension(tmp_path):
    path = tmp_path / "Movie.2025.mkv"
    path.write_bytes(b"not used")

    result = process_one(path, client=object(), cover_dir=tmp_path)

    assert result.status == "skipped"
    assert "unsupported" in result.message


def test_process_one_skips_low_confidence_match(tmp_path):
    class Client:
        def search_best(self, parsed):
            return None

    path = tmp_path / "Unknown.2025.mp4"
    path.write_bytes(b"not an actual mp4")

    result = process_one(path, Client(), tmp_path)

    assert result.status == "skipped"
    assert "no confident" in result.message


def test_process_one_success_with_mocked_media(tmp_path, monkeypatch):
    class Client:
        def search_best(self, parsed):
            return MovieMetadata(
                tmdb_id=1,
                year=2025,
                chinese_title="火遮眼",
                original_title="",
                display_title="2025 火遮眼",
                poster_path="/poster.jpg",
                confidence=0.9,
            )

        def poster_url(self, poster_path):
            return "https://image.tmdb.org/t/p/w780/poster.jpg"

    original = tmp_path / "火遮眼.2025.mp4"
    original.write_bytes(b"fake mp4")
    calls = []

    monkeypatch.setattr("mediatag.pipeline.download_image", lambda url: b"raw")
    monkeypatch.setattr("mediatag.pipeline.normalize_poster", lambda data: b"jpg")

    def fake_faststart(path, ffmpeg="ffmpeg"):
        calls.append("faststart")
        return True

    def fake_embed(path, data):
        calls.append("embed")
        return True

    monkeypatch.setattr("mediatag.pipeline.embed_mp4_cover", fake_embed)
    monkeypatch.setattr("mediatag.pipeline.apply_faststart", fake_faststart)

    result = process_one(original, Client(), tmp_path / "covers")

    assert result.status == "done"
    assert result.new_path == tmp_path / "2025 火遮眼.mp4"
    assert result.cover_path == tmp_path / "covers" / "2025 火遮眼.jpg"
    assert result.new_path.exists()
    assert calls == ["faststart", "embed"]


def test_process_one_updates_cover_without_renaming_normalized_file(tmp_path, monkeypatch):
    class Client:
        def search_best(self, parsed):
            return MovieMetadata(
                tmdb_id=1,
                year=2025,
                chinese_title="火遮眼",
                original_title="",
                display_title="2025 火遮眼",
                poster_path="/poster.jpg",
                confidence=0.9,
            )

        def poster_url(self, poster_path):
            return "https://image.tmdb.org/t/p/w780/poster.jpg"

    original = tmp_path / "2025 火遮眼.mp4"
    original.write_bytes(b"fake mp4")

    monkeypatch.setattr("mediatag.pipeline.download_image", lambda url: b"raw")
    monkeypatch.setattr("mediatag.pipeline.normalize_poster", lambda data: b"jpg")
    monkeypatch.setattr("mediatag.pipeline.embed_mp4_cover", lambda path, data: True)
    monkeypatch.setattr("mediatag.pipeline.apply_faststart", lambda path, ffmpeg="ffmpeg": True)

    result = process_one(original, Client(), tmp_path / "covers")

    assert result.status == "done"
    assert result.new_path == original
    assert result.message == "2025 火遮眼.mp4: cover updated"
    assert not (tmp_path / "2025 火遮眼 (1).mp4").exists()
