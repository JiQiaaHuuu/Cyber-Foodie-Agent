from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from .agent_service import build_agents, debate_events, parse_preferences, run_debate
from .config import DEEPSEEK_ENDPOINT, DEEPSEEK_MODEL, PORT, STATIC_DIR


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
    return json.loads(raw or "{}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/health":
            json_response(self, 200, {"ok": True, "model": DEEPSEEK_MODEL})
            return
        path = STATIC_DIR / self.path.lstrip("/")
        if path.exists() and path.is_file():
            content_type = "text/css" if path.suffix == ".css" else "application/javascript"
            self.serve_file(path, content_type + "; charset=utf-8")
            return
        json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/api/debate":
            self.handle_debate()
            return
        if self.path == "/api/debate-stream":
            self.handle_debate_stream()
            return
        json_response(self, 404, {"error": "not found"})

    def handle_debate(self) -> None:
        try:
            body = read_body(self)
            result = run_debate(parse_preferences(body), build_agents(body))
            json_response(self, 200, result)
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})

    def handle_debate_stream(self) -> None:
        try:
            body = read_body(self)
            prefs = parse_preferences(body)
            agents = build_agents(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            for event in debate_events(prefs, agents):
                self.wfile.write(json.dumps(event, ensure_ascii=False).encode("utf-8") + b"\n")
                self.wfile.flush()
        except Exception as exc:
            self.wfile.write(json.dumps({"type": "error", "error": str(exc)}, ensure_ascii=False).encode("utf-8") + b"\n")
            self.wfile.flush()

    def serve_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"CyberFoodie Agent running at http://127.0.0.1:{PORT}", flush=True)
    print(f"DeepSeek endpoint: {DEEPSEEK_ENDPOINT}, model: {DEEPSEEK_MODEL}", flush=True)
    server.serve_forever()
