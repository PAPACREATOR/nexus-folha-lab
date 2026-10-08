"""Real HTTP round-trip to a *fake local* llama.cpp-compatible endpoint.

This test proves transport and failure behaviour, not actual model quality.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from folha_lab import local_ai


class LocalModelStub(BaseHTTPRequestHandler):
    seen = []
    reply = None
    status = 200

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        raw = self.rfile.read(length)
        type(self).seen.append((self.path, json.loads(raw)))
        data = type(self).reply
        self.send_response(type(self).status)
        if type(self).status == 302:
            self.send_header("Location", "https://example.com/outside")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if data:
            self.wfile.write(data)

    def log_message(self, *_args):
        pass


def _response(message):
    return json.dumps(
        {"choices": [{"message": {"content": message}}]}, ensure_ascii=False
    ).encode("utf-8")


def test_real_loopback_http_model_roundtrip_and_no_redirect(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalModelStub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("FOLHA_LOCAL_AI", "1")
        monkeypatch.setattr(
            local_ai, "LOCAL_URL",
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
        )
        LocalModelStub.seen = []
        LocalModelStub.status = 200
        LocalModelStub.reply = _response(
            '{"question":"Queres apenas falar sobre o texto ou guardá-lo?"}'
        )
        suggestion = local_ai.suggest_question("Parece-me um tema.")
        assert suggestion == "Queres apenas falar sobre o texto ou guardá-lo?"
        assert len(LocalModelStub.seen) == 1
        path, payload = LocalModelStub.seen[0]
        assert path == "/v1/chat/completions"
        assert payload["model"] == "nexus-qwen3-1.7b"
        assert payload["messages"][1]["content"] == "Parece-me um tema."

        LocalModelStub.status = 302
        LocalModelStub.reply = b""
        assert local_ai.suggest_question("Pedido indeciso") is None
        assert len(LocalModelStub.seen) == 2

        LocalModelStub.status = 200
        LocalModelStub.reply = _response("not valid json")
        assert local_ai.suggest_question("Pedido indeciso") is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
