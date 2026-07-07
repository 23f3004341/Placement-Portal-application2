import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BACKEND_ORIGIN = os.environ.get("BACKEND_ORIGIN", "http://127.0.0.1:5000")
DIST_DIR = os.path.join(os.path.dirname(__file__), "dist")
PROXY_PREFIXES = ("/api/", "/static/uploads/", "/static/exports/")
PROXY_EXACT = {"/service-worker.js"}


class PlacementPortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def do_GET(self):
        if self._should_proxy():
            self._proxy()
            return
        if not self._asset_exists():
            self.path = "/index.html"
        super().do_GET()

    def do_HEAD(self):
        if self._should_proxy():
            self._proxy()
            return
        if not self._asset_exists():
            self.path = "/index.html"
        super().do_HEAD()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def _should_proxy(self):
        return self.path in PROXY_EXACT or self.path.startswith(PROXY_PREFIXES)

    def _asset_exists(self):
        request_path = self.path.split("?", 1)[0].lstrip("/")
        if not request_path:
            return True
        return os.path.exists(os.path.join(DIST_DIR, request_path))

    def _proxy(self):
        body = None
        if "Content-Length" in self.headers:
            body = self.rfile.read(int(self.headers["Content-Length"]))

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        request = Request(
            BACKEND_ORIGIN + self.path,
            data=body,
            headers=headers,
            method=self.command,
        )
        try:
            with urlopen(request, timeout=30) as response:
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                        self.send_header(key, value)
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(response.read())
        except HTTPError as exc:
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                    self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(exc.read())
        except URLError as exc:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Backend proxy error: {exc}".encode("utf-8"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("127.0.0.1", port), PlacementPortalHandler)
    print(f"Serving Vue dist with API proxy at http://localhost:{port}")
    print(f"Proxying backend requests to {BACKEND_ORIGIN}")
    server.serve_forever()
