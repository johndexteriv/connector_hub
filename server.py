#!/usr/bin/env python3
"""
AI Connector Hub — Web UI Server
Zero dependencies — pure Python stdlib.

Usage:
  python server.py                     # localhost:8080
  python server.py --port 3000
  python server.py --host 0.0.0.0      # expose to network (for hosted use)
"""

import argparse
import json
import sys
import webbrowser
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent))

from catalog import CATALOG
from detectors import ALL_DETECTORS
from reporter import build_summary

UI_DIR = Path(__file__).parent / "ui"


def run_scan(path: str) -> dict:
    root = Path(path).resolve()
    if not root.exists():
        return {"error": f"Path does not exist: {path}"}

    all_detections = []
    for DetectorClass in ALL_DETECTORS:
        detector = DetectorClass(root=root, catalog=CATALOG)
        all_detections.extend(detector.detect())

    summary = build_summary(all_detections)

    by_category: dict[str, list] = defaultdict(list)
    for tool in summary.values():
        by_category[tool["category"]].append(tool)

    # Sort tools within each category alphabetically
    for cat in by_category:
        by_category[cat].sort(key=lambda t: t["label"])

    return {
        "scanned_path": str(root),
        "tool_count": len(summary),
        "signal_count": len(all_detections),
        "tools": sorted(summary.values(), key=lambda t: (t["category"], t["label"])),
        "by_category": dict(by_category),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        method = args[0] if args else ""
        status = args[1] if len(args) > 1 else ""
        # Only log API calls
        if "/api/" in str(method):
            print(f"  {status}  {method}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_response(404)
            self.end_headers()
            return
        types = {".html": "text/html", ".css": "text/css",
                 ".js": "application/javascript", ".json": "application/json"}
        ct = types.get(path.suffix, "text/plain")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{ct}; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/api/scan":
            path = qs.get("path", [str(Path.cwd())])[0]
            self._send_json(run_scan(path))

        elif parsed.path == "/api/catalog":
            self._send_json(CATALOG)

        elif parsed.path in ("/", "/index.html"):
            self._serve_file(UI_DIR / "index.html")

        else:
            self._serve_file(UI_DIR / parsed.path.lstrip("/"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/scan":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}
        self._send_json(run_scan(data.get("path", str(Path.cwd()))))


def main():
    parser = argparse.ArgumentParser(description="AI Connector Hub — Web UI")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1",
                        help="Use 0.0.0.0 to expose on network (hosted mode)")
    parser.add_argument("--no-open", action="store_true",
                        help="Don't auto-open browser")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}"

    print(f"\n  ╔═══════════════════════════╗")
    print(f"  ║   AI CONNECTOR HUB UI     ║")
    print(f"  ╚═══════════════════════════╝")
    print(f"\n  URL  →  {url}")
    print(f"  Mode →  {'hosted (0.0.0.0)' if args.host == '0.0.0.0' else 'local'}")
    print(f"\n  Ctrl+C to stop\n")

    if not args.no_open and args.host != "0.0.0.0":
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.\n")


if __name__ == "__main__":
    main()
