"""HTTP isolation gates: the local model is not a second execution path."""
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest

from folha_lab import server


def send(base, text):
    data = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
    request = Request(
        base + "/interpret", method="POST", data=data,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=5) as response:
        return json.load(response)


@pytest.fixture
def endpoint():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    runner = threading.Thread(target=httpd.serve_forever, daemon=True)
    runner.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        runner.join(timeout=5)


def test_unresolved_uses_local_question_only(endpoint, monkeypatch):
    inputs = []

    def model(text):
        inputs.append(text)
        return "Queres guardar este texto ou procurar uma fonte?"

    monkeypatch.setattr(server, "suggest_question", model)
    answer = send(endpoint, "Estou na dúvida.")
    assert answer["status"] == "UNRESOLVED"
    assert answer["question_source"] == "local_model"
    assert answer["question"].endswith("?")
    assert answer["confirmation_required"] is False
    assert answer["execution"] == "SIMULATED_ONLY"
    assert inputs == ["Estou na dúvida."]


def test_resolved_prefix_and_blocked_never_invoke_ai(endpoint, monkeypatch):
    def forbidden(_text):
        pytest.fail("Model must never run unless natural intent is unresolved")

    monkeypatch.setattr(server, "suggest_question", forbidden)
    for text in ["Guarda este texto", "@@ documento", "@@", "\x00"]:
        result = send(endpoint, text)
        assert result["execution"] == "SIMULATED_ONLY"
    assert send(endpoint, "Guarda este texto")["confirmation_required"] is True


def test_ai_failure_retains_deterministic_question(endpoint, monkeypatch):
    monkeypatch.setattr(server, "suggest_question", lambda _text: None)
    response = send(endpoint, "Não percebi isto")
    assert response["status"] == "UNRESOLVED"
    assert response["question_source"] == "deterministic"
    assert "explicar" in response["question"]
    assert response["confirmation_required"] is False
