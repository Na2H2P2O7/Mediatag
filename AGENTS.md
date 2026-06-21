# AGENTS.md

This repository is the clean public version of Movie Cover Tagger.

## What this project is

Movie Cover Tagger is a Python desktop and CLI tool that batch-processes local
movie MP4 files:

- parses noisy release filenames,
- searches TMDb for movie metadata,
- downloads poster art,
- embeds the poster into MP4 cover metadata,
- renames the file into a clean movie-library format.

v1 intentionally supports MP4 movies only. Other containers, including MKV, are
detected and skipped with a clear message.

## Public repo rules

- Keep this repository clean and portfolio-safe.
- Do not copy private sample media, generated covers, build outputs, local
  virtual environments, or old project history into this repo.
- Do not commit `.env` or TMDb credentials.
- Do not reintroduce legacy scraper/domain-specific naming from the private
  predecessor project.
- Keep UI changes visually close to the original desktop shell unless the user
  explicitly asks for a redesign.

## Commands

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the GUI:

```bash
movie-cover-tagger-gui
```

Run the CLI:

```bash
movie-cover-tagger --dir "/path/to/movies" --yes
```

`TMDB_BEARER_TOKEN` or `TMDB_API_KEY` must be set in `.env` or the environment
before real TMDb lookups will work.

## Architecture

- `src/movie_cover_tagger/parser.py` parses release filenames into title
  candidates and release year.
- `src/movie_cover_tagger/tmdb.py` wraps TMDb search/detail/poster metadata.
- `src/movie_cover_tagger/media.py` handles poster normalization, MP4 cover
  embedding, and optional ffmpeg faststart.
- `src/movie_cover_tagger/pipeline.py` ties parsing, lookup, embedding, saving,
  and renaming together.
- `src/movie_cover_tagger/gui_app.py` exposes the PyWebView bridge.
- `src/movie_cover_tagger/gui/` is plain HTML/CSS/JS and intentionally mirrors
  the original app shell.

## Packaging notes

macOS Finder-launched apps inherit a minimal PATH. Keep the Homebrew PATH
repair in `gui_app.py` so packaged apps can find ffmpeg when it is installed at
`/opt/homebrew/bin/ffmpeg`.

PyInstaller builds should include:

- `--add-data "src/movie_cover_tagger/gui:movie_cover_tagger/gui"`
- `--paths "src"`
- `--icon "assets/icon.icns"`

The GitHub Actions workflow in `.github/workflows/build-macos.yml` is the
canonical macOS build command.
