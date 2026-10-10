"""Fail-first loopback browser boundary tests; no Nexus Host or side effects.

HTTP Host/Origin are untrusted even when a service listens on 127.0.0.1:
these tests send TCP traffic to loopback with hostile request headers.
"""
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from folha_lab.server import Handler


@contextmanager
def local_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def query(base, method="POST", *, host=None, origin=None):
    headers = {}
    if host is not None:
        headers["Host"] = host
    if origin is not None:
        headers["Origin"] = origin
    data = None
    url = base + "/"
    if method == "POST":
        url = base + "/interpret"
        headers["Content-Type"] = "application/json"
        data = json.dumps({"text": "Guarda esta nota."}).encode("utf-8")
    request = Request(url, headers=headers, data=data, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("host", [
    "website.example",
    "website.example:8765",
    "127.0.0.1",
    "127.0.0.1:9999",
    "localhost:8765",
])
def test_foreign_host_cannot_use_loopback_lab(method, host):
    with local_server() as base:
        code, _ = query(base, method, host=host)
    assert code == 403


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("origin", [
    "https://foreign.example",
    "http://foreign.example",
    "null",
    "http://127.0.0.1:9999",
])
def test_foreign_origin_cannot_use_loopback_lab(method, origin):
    with local_server() as base:
        code, _ = query(base, method, origin=origin)
    assert code == 403


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_real_local_browser_headers_still_work(method):
    with local_server() as base:
        code, raw = query(base, method, origin=base)
    assert code == 200
    if method == "POST":
        result = json.loads(raw)
        assert result["execution"] == "SIMULATED_ONLY"
        assert result["original"] == "Guarda esta nota."
        assert result["confirmation_required"] is True


def test_foreign_post_is_rejected_before_parser(monkeypatch):
    import folha_lab.server as module

    def forbidden(*_args, **_kwargs):
        pytest.fail("Untrusted browser origin reached interpretation")

    monkeypatch.setattr(module, "parse", forbidden)
    with local_server() as base:
        assert query(base, "POST", origin="https://foreign.example")[0] == 403
        assert query(base, "POST", host="foreign.example")[0] == 403
