# CLAUDE.md

This file gives Claude Code project-specific context for Mediatag.

## Project summary

Mediatag is a clean public Python project for batch-tagging movie MP4
files. It uses TMDb metadata, downloads poster art, embeds the poster into MP4
metadata with Mutagen, and renames files into a clean library format such as:

```text
2025 火遮眼.mp4
2010 盗梦空间 Inception.mp4
```

The app has both:

- a PyWebView desktop GUI,
- a CLI entry point via `mediatag`.

## Development commands

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run from source:

```bash
mediatag-gui
mediatag --dir "/path/to/movies" --yes
```

Real TMDb calls require `TMDB_BEARER_TOKEN` or `TMDB_API_KEY` in `.env` or the
environment.

## Important constraints

- This is a portfolio-safe public repository.
- Do not commit media files, downloaded posters, credentials, virtualenvs, or
  build artifacts.
- v1 is MP4-only. Unsupported formats should be skipped, not partially handled.
- The GUI should visually stay close to the original desktop shell unless a
  redesign is explicitly requested.
- Keep file operations safe: never overwrite an existing target filename.

## Code map

- `parser.py`: noisy movie filename parsing.
- `tmdb.py`: TMDb API client and metadata formatting.
- `media.py`: image normalization, MP4 cover embedding, optional faststart.
- `pipeline.py`: batch processing orchestration.
- `gui_app.py`: Python bridge for PyWebView.
- `gui/`: static HTML/CSS/JS shell.

## Testing expectations

Prefer mocked TMDb tests for normal CI. The live TMDb smoke test is intentionally
gated behind `TMDB_BEARER_TOKEN`.
