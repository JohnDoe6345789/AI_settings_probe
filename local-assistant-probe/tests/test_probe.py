import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Tuple

from local_assistant_probe.probe import _best_effort_probe


class _Handler(BaseHTTPRequestHandler):
    routes: Dict[Tuple[str, str], Tuple[int, Dict[str, str], Any]] = {}
    token: str = "Bearer sk-test"

    def _send(self, code: int, headers: Dict[str, str], body: bytes) -> None:
        self.send_response(code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self) -> bool:
        return self.headers.get("Authorization") == self.token

    def do_GET(self) -> None:  # noqa: N802
        key = ("GET", self.path)
        if not self._auth_ok():
            self._send(401, {"Content-Type": "application/json"}, b'{"error":"unauthorized"}')
            return
        if key not in self.routes:
            self._send(404, {"Content-Type": "application/json"}, b'{"error":"not_found"}')
            return
        code, hdrs, payload = self.routes[key]
        body = json.dumps(payload).encode("utf-8")
        self._send(code, {"Content-Type": "application/json", **hdrs}, body)

    def do_POST(self) -> None:  # noqa: N802
        key = ("POST", self.path)
        if not self._auth_ok():
            self._send(401, {"Content-Type": "application/json"}, b'{"error":"unauthorized"}')
            return
        if key not in self.routes:
            self._send(404, {"Content-Type": "application/json"}, b'{"error":"not_found"}')
            return
        code, hdrs, payload = self.routes[key]
        body = json.dumps(payload).encode("utf-8")
        self._send(code, {"Content-Type": "application/json", **hdrs}, body)

    def log_message(self, format: str, *args: Any) -> None:
        return


class ProbeTests(unittest.TestCase):
    def _run_server(self, routes: Dict[Tuple[str, str], Tuple[int, Dict[str, str], Any]]) -> Tuple[HTTPServer, int]:
        _Handler.routes = routes
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.05)
        return server, int(port)

    def test_finds_api_base_and_chat(self) -> None:
        routes = {
            ("GET", "/api/models"): (200, {}, {"data": [{"id": "llama3:latest"}]}),
            ("POST", "/api/chat/completions"): (200, {}, {"choices": [{"message": {"content": "pong"}}]}),
        }
        server, port = self._run_server(routes)
        try:
            res, _ = _best_effort_probe("127.0.0.1", port, "sk-test", "llama3", 1.0)
            self.assertIsNotNone(res)
            assert res is not None
            self.assertEqual(res.api_base, f"http://127.0.0.1:{port}/api")
            self.assertEqual(res.model, "llama3:latest")
            self.assertFalse(res.use_legacy_completions_endpoint)
        finally:
            server.shutdown()

    def test_falls_back_to_legacy_completions(self) -> None:
        routes = {
            ("GET", "/api/models"): (200, {}, {"data": [{"id": "llama3:latest"}]}),
            ("POST", "/api/chat/completions"): (404, {}, {"error": "nope"}),
            ("POST", "/api/completions"): (200, {}, {"choices": [{"text": "pong"}]}),
        }
        server, port = self._run_server(routes)
        try:
            res, _ = _best_effort_probe("127.0.0.1", port, "sk-test", "llama3", 1.0)
            self.assertIsNotNone(res)
            assert res is not None
            self.assertTrue(res.use_legacy_completions_endpoint)
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
