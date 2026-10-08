"""LanguageTool localhost wire checks and server fallback precedence."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

import pytest

from folha_lab import local_language, server


def corrected():
    return {
        "warnings": {"incompleteResults": False},
        "matches": [{
            "offset": 0, "length": 6,
            "replacements": [{"value": "Corrige"}],
        }],
    }


class StubLanguageTool(BaseHTTPRequestHandler):
    requests = []
    reply = corrected()
    status = 200

    def do_POST(self):
        size = int(self.headers["Content-Length"])
        query = parse_qs(self.rfile.read(size).decode("utf-8"))
        type(self).requests.append((self.path, query))
        self.send_response(type(self).status)
        if type(self).status == 302:
            self.send_header("Location", "https://example.com/never-visit")
        self.end_headers()
        if type(self).status == 200:
            self.wfile.write(json.dumps(type(self).reply).encode("utf-8"))

    def log_message(self, *_args):
        pass


def test_opt_in_language_tool_is_local_and_fails_closed(monkeypatch):
    local = ThreadingHTTPServer(("127.0.0.1", 0), StubLanguageTool)
    thread = threading.Thread(target=local.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("FOLHA_LOCAL_LT", "1")
        monkeypatch.setattr(local_language, "LOCAL_LT_URL",
                            f"http://127.0.0.1:{local.server_port}/v2/check")
        StubLanguageTool.requests = []
        StubLanguageTool.reply = corrected()
        StubLanguageTool.status = 200
        diagnostic = local_language.local_diagnostic("Corige o texto")
        assert diagnostic == corrected()
        assert StubLanguageTool.requests == [
            ("/v2/check", {"text": ["Corige o texto"], "language": ["pt-PT"]})
        ]
        StubLanguageTool.status = 302
        assert local_language.local_diagnostic("Corige o texto") is None
        StubLanguageTool.status = 200
        StubLanguageTool.reply = {"warnings": {"incompleteResults": True}, "matches": []}
        assert local_language.local_diagnostic("Corige o texto") is None
    finally:
        local.shutdown()
        local.server_close()
        thread.join(timeout=5)


def test_local_language_tool_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FOLHA_LOCAL_LT", raising=False)
    monkeypatch.setattr(
        local_language, "build_opener",
        lambda *_a: pytest.fail("No network permitted"),
    )
    assert local_language.local_diagnostic("Corige o texto") is None


def test_backend_uses_lt_before_ai(monkeypatch):
    monkeypatch.setattr(server, "local_diagnostic", lambda _t: corrected())

    def must_not_run(_t):
        pytest.fail("LanguageTool recovered the intent; do not contact AI")

    monkeypatch.setattr(server, "suggest_question", must_not_run)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        body = json.dumps({"text": "Corige o texto"}).encode("utf-8")
        req = Request(f"http://127.0.0.1:{httpd.server_port}/interpret",
                      data=body, method="POST",
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=5) as response:
            output = json.load(response)
        assert output["intent"] == "trabalhar"
        assert output["parser"] == "languagetool-shadow+eliza-v1"
        assert output["original"] == "Corige o texto"
        assert output["shadow"] == "Corrige o texto"
        assert output["confirmation_required"] is True
        assert output["execution"] == "SIMULATED_ONLY"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
