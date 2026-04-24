from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import costs_api, pricing_api, products_api, sales_api, stats_api
from .shared import ApiServices, create_services, json_response, parse_request, serialize


SERVICES = create_services()
HANDLERS = [
    products_api.handle,
    costs_api.handle,
    pricing_api.handle,
    sales_api.handle,
    stats_api.handle,
]


class OdinApiHandler(BaseHTTPRequestHandler):
    server_version = "OdinAPI/1.0"

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PATCH(self) -> None:
        self._dispatch("PATCH")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def _dispatch(self, method: str) -> None:
        try:
            request = parse_request(method, self.path, self._read_body())
            response = self._resolve(request, SERVICES)
        except ValueError as error:
            response = json_response(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except json.JSONDecodeError:
            response = json_response(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body."})
        except Exception as error:
            response = json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
        self._send_json(response.status, response.payload)

    def _resolve(self, request, services: ApiServices):
        if request.path == "/api/health":
            return json_response(200, {"status": "ok"})
        for handler in HANDLERS:
            response = handler(request, services)
            if response is not None:
                return response
        return json_response(HTTPStatus.NOT_FOUND, {"error": "Route not found."})

    def _read_body(self) -> bytes:
        content_length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(content_length) if content_length > 0 else b""

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(serialize(payload), ensure_ascii=True).encode("utf-8")
        self.send_response(int(status))
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args) -> None:
        return


def run_api(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), OdinApiHandler)
    print(f"Odin API listening on http://{host}:{port}")
    server.serve_forever()
