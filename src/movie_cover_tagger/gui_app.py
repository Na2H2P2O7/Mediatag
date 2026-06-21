from __future__ import annotations

import json
import os
import platform
import sys
import threading
import time
from pathlib import Path

import webview

from .config import TMDbCredentials, default_cover_dir, load_tmdb_credentials
from .pipeline import process_files


if platform.system() == "Darwin":
    extra_paths = ["/opt/homebrew/bin", "/usr/local/bin"]
    current = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join(extra_paths + [p for p in current.split(os.pathsep) if p])


class Api:
    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self.cover_dir = default_cover_dir()
        self.credentials = load_tmdb_credentials()

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def init_app(self) -> dict[str, str]:
        return {
            "coverDir": str(self.cover_dir),
            "hasToken": "yes" if self.credentials.is_configured else "no",
        }

    def minimize(self) -> None:
        if self._window:
            self._window.minimize()

    def close(self) -> None:
        if not self._window:
            return
        if platform.system() == "Darwin":
            def deferred_close() -> None:
                time.sleep(0.2)
                self._window.destroy()

            threading.Thread(target=deferred_close, daemon=True).start()
        else:
            self._window.destroy()

    def toggle_maximize(self) -> None:
        if self._window:
            self._window.toggle_fullscreen()

    def select_cover_folder(self) -> None:
        if not self._window:
            return
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if result:
            self.cover_dir = Path(result[0])
            self._eval("window.setCoverDir(%s)" % json.dumps(str(self.cover_dir)))

    def select_folder(self) -> None:
        self.select_cover_folder()

    def set_token(self, token: str) -> str:
        self.credentials = TMDbCredentials(bearer_token=token.strip() or None)
        return "OK"

    def start_batch(self) -> None:
        self.start_javcover()

    def start_javcover(self) -> None:
        if not self._window:
            return
        files = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=True,
            file_types=("Media Files (*.mp4;*.mkv;*.avi;*.mov)", "All files (*.*)"),
        )
        if not files:
            return
        threading.Thread(target=self._run_batch, args=(files, True), daemon=True).start()

    def start_manual(self) -> None:
        if not self._window:
            return
        files = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=True,
            file_types=("MP4 Files (*.mp4)", "All files (*.*)"),
        )
        if not files:
            return
        threading.Thread(target=self._run_batch, args=(files, False), daemon=True).start()

    def _run_batch(self, files: list[str], run_faststart: bool) -> None:
        self._eval("window.resetUi()")
        if not self.credentials.is_configured:
            self._eval("window.appendLog('Missing TMDb credentials. Set TMDB_BEARER_TOKEN or TMDB_API_KEY in .env first.\\n')")
            self._eval("window.updateProgress(0, %d, 'Missing TMDb credentials', 0)" % len(files))
            return

        def progress(current: int, total: int, message: str, pct: int | None) -> None:
            self._eval(
                "window.updateProgress(%d, %d, %s, %s)"
                % (current, total, json.dumps(message), "null" if pct is None else pct)
            )

        def log(message: str) -> None:
            self._eval("window.appendLog(%s)" % json.dumps(message + "\n"))

        def cover(path: Path) -> None:
            self._eval("window.setCover(%s)" % json.dumps(path.resolve().as_uri()))

        process_files(
            files,
            self.credentials,
            self.cover_dir,
            progress=progress,
            log=log,
            cover=cover,
            run_faststart=run_faststart,
        )
        self._eval("window.updateProgress(%d, %d, 'All done.', 100)" % (len(files), len(files)))

    def _eval(self, script: str) -> None:
        if self._window:
            try:
                self._window.evaluate_js(script)
            except Exception:
                pass


def main() -> None:
    api = Api()
    gui_dir = Path(__file__).with_name("gui")
    url = (gui_dir / "index.html").resolve().as_uri()
    window = webview.create_window(
        "MovieCover",
        url,
        js_api=api,
        width=737,
        height=640,
        min_size=(737, 560),
        frameless=True,
        easy_drag=platform.system() == "Darwin",
        background_color="#FFFFFF",
    )
    api.set_window(window)
    backend = "edgechromium" if platform.system() == "Windows" else None
    webview.start(debug=False, gui=backend)


if __name__ == "__main__":
    main()
