# Mediatag

Mediatag is a small desktop and CLI tool for cleaning up movie MP4
files. It looks up movie metadata on TMDb, downloads the poster, embeds it into
the MP4 cover-art metadata, and renames the file into a clean library format.

## Features

- Batch process local movie files from a native PyWebView desktop app.
- Automatically search TMDb by parsed title and release year.
- Save downloaded posters to a local `covers/` folder.
- Embed poster art into MP4 metadata with Mutagen.
- Rename files into a clean format:
  - Chinese title only: `2025 火遮眼.mp4`
  - Chinese + original title: `2010 盗梦空间 Inception.mp4`
- Skip MKV/AVI/MOV and other formats clearly. v1 is MP4-only.
- Never overwrite existing files; name collisions become ` (1)`, ` (2)`, etc.

## Requirements

- Python 3.10+
- A TMDb API read access token
- Optional: FFmpeg for MP4 faststart optimization

Create TMDb API credentials from the official TMDb API settings page:
<https://developer.themoviedb.org/docs/authentication-application>

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Put either a Read Access Token or a v3 API key in `.env`:

```bash
TMDB_BEARER_TOKEN=your_read_access_token
# or
TMDB_API_KEY=your_v3_api_key
```

## Run The Desktop App

```bash
mediatag-gui
```

The app reads TMDb credentials from `.env` or your environment.

## CLI Usage

Process a directory:

```bash
mediatag --dir "/path/to/movies" --yes
```

Process specific files:

```bash
mediatag "/path/to/Movie.2025.1080p.mp4" --yes
```

Skip FFmpeg faststart:

```bash
mediatag --dir "/path/to/movies" --yes --no-faststart
```

## Notes

- v1 supports MP4 files only because MP4 and MKV store cover art differently.
- The parser is designed for common noisy release names such as
  `Overheard.3.2014.BluRay.1080p.x265.10bit.2Audio.mp4`.
- `.env`, media files, downloaded covers, and build artifacts are ignored by
  git.

## Development

```bash
pytest
```

Run the real TMDb smoke test only when a token is available:

```bash
TMDB_BEARER_TOKEN=... pytest tests/test_tmdb_live.py
```

## Build macOS App

The GitHub Actions workflow builds a macOS `.dmg` through PyInstaller. Locally:

```bash
pyinstaller --noconfirm --windowed --name "Mediatag" \
  --icon "assets/icon.icns" \
  --add-data "src/mediatag/gui:mediatag/gui" \
  --paths "src" \
  mediatag_app.py
```
