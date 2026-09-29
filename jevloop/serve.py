"""
serve.py — tiny static server for dashboard/index.html + token-checked /control endpoint.

Listens on 127.0.0.1:8765 only. No CORS headers. Requires the per-install token.
"""
from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from jevloop.control import get_token, pause, resume, get_state

SKILL_DIR  = Path(__file__).parent.parent
DASH_DIR   = SKILL_DIR / "dashboard"
LOG_DIR    = Path.home() / ".jev-loop"
PORT       = 8765
HOST       = "127.0.0.1"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress access log

    def _send(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            self._serve_file(DASH_DIR / "index.html", "text/html")
        elif path == "/wall.html":
            self._serve_file(DASH_DIR / "wall.html", "text/html")
        elif path == "/latest.json":
            self._serve_file(LOG_DIR / "latest.json", "application/json")
        elif path == "/state":
            body = json.dumps({"state": get_state()}).encode()
            self._send(200, "application/json", body)
        else:
            self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/control":
            self._send(404, "text/plain", b"Not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        token = body.get("token", "")
        action = body.get("action", "")

        if token != get_token():
            self._send(403, "text/plain", b"Forbidden")
            return

        if action == "pause":
            pause()
        elif action == "resume":
            resume()
        else:
            self._send(400, "text/plain", b"Unknown action")
            return

        resp = json.dumps({"state": get_state()}).encode()
        self._send(200, "application/json", resp)

    def _serve_file(self, path: Path, ctype: str):
        if not path.exists():
            self._send(404, "text/plain", b"Not found")
            return
        body = path.read_bytes()
        self._send(200, ctype, body)


def serve():
    token = get_token()  # ensure token exists
    print(f"Dashboard at http://{HOST}:{PORT}")
    print(f"  index.html  — live dashboard with Start / Stop")
    print(f"  wall.html   — wall display")
    print(f"  Ctrl+C to stop")
    server = HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
