"""ARTH GUI Application Entrypoint.
Launches the native macOS window using pywebview with the Jarvis glowing orb interface.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import webview

from arth.config import ArthConfig, load_config
from arth.brain import OllamaManager
from arth.logger import ActivityLogger
from arth.gui.bridge import GUIBridge

GUI_DIR = Path(__file__).resolve().parent
HTML_FILE = GUI_DIR / "templates" / "index.html"


def launch_gui(
    config: Optional[ArthConfig] = None,
    brain: Optional[OllamaManager] = None,
    logger: Optional[ActivityLogger] = None,
    tts: Optional[Any] = None,
    stt: Optional[Any] = None,
    memory: Optional[Any] = None,
    personality: Optional[Any] = None,
) -> None:
    """Launch the ARTH native macOS window with full Jarvis GUI."""
    cfg = config or load_config()
    brn = brain or OllamaManager(cfg)
    log = logger or ActivityLogger()

    # Create the API bridge
    bridge = GUIBridge(cfg, brn, log, memory=memory, personality=personality, tts=tts, stt=stt)

    # Create native window
    window = webview.create_window(
        title="ARTH — Personal AI Assistant",
        url=f"file://{HTML_FILE}",
        js_api=bridge,
        width=1050,
        height=720,
        min_size=(800, 600),
        background_color="#070b14",
    )

    bridge.set_window(window)

    # Start native macOS Cocoa / WebKit GUI loop
    webview.start(debug=False)


import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler


class ArthHTTPHandler(BaseHTTPRequestHandler):
    bridge: Optional[GUIBridge] = None

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_headers(200, "text/plain")

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            if HTML_FILE.exists():
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(HTML_FILE.read_bytes())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"index.html not found")
            return

        # Serve static assets (/assets/...)
        if "/assets/" in path:
            asset_subpath = path[path.find("/assets/") + 1 :]
            file_path = GUI_DIR / asset_subpath
            if file_path.exists() and file_path.is_file():
                mime, _ = mimetypes.guess_type(str(file_path))
                self._set_headers(200, mime or "application/octet-stream")
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Asset not found")
                return

        # API: Initial State
        if path == "/api/state":
            state = self.bridge.get_initial_state() if self.bridge else {"user_name": "Boss"}
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        # API: Logs
        if path == "/api/logs":
            logs = self.bridge.get_logs() if self.bridge else []
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(logs).encode("utf-8"))
            return

        # API: Pending Permission Check
        if path == "/api/permission":
            perm_data = self.bridge.get_pending_permission() if self.bridge else {"waiting": False}
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(perm_data).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"404 Not Found")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {}

        if self.path == "/api/chat":
            message = data.get("message", "")
            if not self.bridge:
                self._set_headers(500, "application/json")
                self.wfile.write(json.dumps({"error": "Bridge not initialized"}).encode("utf-8"))
                return

            # Backend TTSEngine handles single authoritative Jarvis voice (Daniel / en-GB-RyanNeural)
            result = self.bridge.send_message(message, speak=True)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if self.path == "/api/voice/listen":
            if not self.bridge:
                self._set_headers(500, "application/json")
                self.wfile.write(json.dumps({"error": "Bridge not initialized"}).encode("utf-8"))
                return
            duration = float(data.get("duration", 4.0))
            lang = data.get("lang", "en")
            result = self.bridge.listen_voice(duration=duration, lang=lang)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if self.path == "/api/permission":
            approved = bool(data.get("approved", False))
            if self.bridge:
                self.bridge.resolve_permission(approved)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "ok", "approved": approved}).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def log_message(self, format: str, *args: Any) -> None:
        pass


def run_web_server(
    port: int = 8501,
    host: str = "127.0.0.1",
    config: Optional[ArthConfig] = None,
    brain: Optional[OllamaManager] = None,
    logger: Optional[ActivityLogger] = None,
    tts: Optional[Any] = None,
    stt: Optional[Any] = None,
    memory: Optional[Any] = None,
    personality: Optional[Any] = None,
) -> None:
    """Launch ARTH Web Interface on specified port and address."""
    cfg = config or load_config()
    brn = brain or OllamaManager(cfg)
    log = logger or ActivityLogger()

    bridge = GUIBridge(cfg, brn, log, memory=memory, personality=personality, tts=tts, stt=stt)
    ArthHTTPHandler.bridge = bridge

    server = HTTPServer((host, port), ArthHTTPHandler)
    print(f"ARTH Web Interface is LIVE at: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down ARTH Web Server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    launch_gui()
