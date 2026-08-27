#!/usr/bin/env python3
"""
Vendor scenario control for the Northstar lab.

POST   /scenarios/{name}/activate
DELETE /scenarios
GET    /scenarios

Talks to WireMock admin API. Stdlib only.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WIREMOCK = os.environ.get("WIREMOCK_URL", "http://localhost:8090").rstrip("/")
SCENARIO_DIR = Path(os.environ.get("SCENARIOS_DIR", str(Path(__file__).resolve().parent.parent / "scenarios")))
ACTIVE: list[str] = []

SCENARIOS = {
    "ledgerlink-empty-200": "HTTP 200 with empty accounts list (stale connection)",
    "optiscan-degraded": "Confident but wrong OCR on scanned or faxed inputs",
    "corveil-ratelimit": "429 responses with long delay",
    "sentinel-no-reason-codes": "Score returned with reasonCodes absent",
    "loancore-batch-window": "503 outside the 02:00-04:00 ET batch window",
    "corveil-slow": "40 second credit report responses",
}


def wiremock(method: str, path: str, body: dict | None = None) -> tuple[int, str]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{WIREMOCK}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()
    except Exception as exc:  # noqa: BLE001
        return 503, str(exc)


def _load_stubs(name: str) -> list[dict]:
    """Load stubs from scenarios/{name}.json or scenarios/{name}/*.json."""
    stubs: list[dict] = []
    flat = SCENARIO_DIR / f"{name}.json"
    if flat.exists():
        stubs.append(json.loads(flat.read_text()))
    folder = SCENARIO_DIR / name
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            payload = json.loads(path.read_text())
            if isinstance(payload, list):
                stubs.extend(payload)
            elif isinstance(payload, dict) and "mappings" in payload:
                stubs.extend(payload["mappings"])
            else:
                stubs.append(payload)
    return stubs


def activate(name: str) -> tuple[int, dict]:
    if name not in SCENARIOS:
        return 404, {"error": f"unknown scenario {name}", "known": list(SCENARIOS)}
    stubs = _load_stubs(name)
    if not stubs:
        return 500, {"error": f"no stub files for {name} under {SCENARIO_DIR}"}
    details = []
    for stub in stubs:
        stub = dict(stub)
        stub["priority"] = 1
        status, raw = wiremock("POST", "/__admin/mappings", stub)
        details.append({"status": status, "detail": raw[:160]})
        if status >= 400:
            return status, {"error": "wiremock rejected stub", "detail": raw}
    if name not in ACTIVE:
        ACTIVE.append(name)
    return 200, {"activated": name, "stubs": len(stubs), "wiremock": details}


def clear_all() -> tuple[int, dict]:
    status, raw = wiremock("POST", "/__admin/mappings/reset")
    ACTIVE.clear()
    return status, {"cleared": True, "wiremockStatus": status, "detail": raw[:200]}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/scenarios":
            self._send(
                200,
                {
                    "available": SCENARIOS,
                    "active": list(ACTIVE),
                },
            )
            return
        if self.path.rstrip("/") in ("/health", "/"):
            self._send(200, {"status": "ok"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parts = self.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "scenarios" and parts[2] == "activate":
            code, payload = activate(parts[1])
            self._send(code, payload)
            return
        self._send(404, {"error": "not found"})

    def do_DELETE(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/scenarios":
            code, payload = clear_all()
            self._send(200 if code < 400 else code, payload)
            return
        self._send(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        print(f"[scenario-control] {self.address_string()} {fmt % args}", flush=True)


def main() -> None:
    port = int(os.environ.get("PORT", "8099"))
    print(f"scenario-control on {port}, wiremock={WIREMOCK}, scenarios={SCENARIO_DIR}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
