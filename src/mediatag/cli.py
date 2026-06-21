from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import TMDbCredentials, default_cover_dir, load_tmdb_credentials
from .pipeline import process_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch tag MP4 movie files with TMDb posters.")
    parser.add_argument("--dir", type=Path, help="Directory to scan for media files.")
    parser.add_argument("files", nargs="*", type=Path, help="Specific files to process.")
    parser.add_argument("--cover-dir", type=Path, default=default_cover_dir(), help="Where downloaded posters are saved.")
    parser.add_argument("--token", help="TMDb bearer token. Defaults to TMDB_BEARER_TOKEN from .env/environment.")
    parser.add_argument("--api-key", help="TMDb v3 API key. Defaults to TMDB_API_KEY from .env/environment.")
    parser.add_argument("--yes", action="store_true", help="Confirm live rename/embed processing.")
    parser.add_argument("--no-faststart", action="store_true", help="Skip ffmpeg faststart after embedding.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env_credentials = load_tmdb_credentials()
    credentials = TMDbCredentials(
        bearer_token=args.token or env_credentials.bearer_token,
        api_key=args.api_key or env_credentials.api_key,
    )
    if not credentials.is_configured:
        print("Missing TMDb credentials. Set TMDB_BEARER_TOKEN or TMDB_API_KEY in .env.", file=sys.stderr)
        return 2
    if not args.yes:
        print("This command modifies MP4 metadata and renames files. Re-run with --yes to continue.", file=sys.stderr)
        return 2

    files = list(args.files)
    if args.dir:
        files.extend(sorted(path for path in args.dir.iterdir() if path.is_file()))
    if not files:
        print("No files provided.", file=sys.stderr)
        return 2

    def log(message: str) -> None:
        print(message)

    results = process_files(files, credentials, args.cover_dir, log=log, run_faststart=not args.no_faststart)
    failed = [result for result in results if result.status == "error"]
    return 1 if failed else 0
