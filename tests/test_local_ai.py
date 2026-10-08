"""The optional model can *only* help phrase a question, never approve actions."""
import json
from urllib.error import HTTPError, URLError

import pytest

from folha_lab import local_ai


class FakeResponse:
    status = 200

    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, n):
        return self.body[:n]


def model_response(value):
    return json.dumps(
        {"choices": [{"message": {"content": value}}]},
        ensure_ascii=False,
    ).encode("utf-8")


def enable_with_fake(monkeypatch, response):
    monkeypatch.setenv("FOLHA_LOCAL_AI", "1")
    calls = []

    class FakeOpener:
        def open(self, req, *, timeout):
            calls.append((req, timeout))
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(local_ai, "build_opener", lambda *_args: FakeOpener())
    return calls


def test_default_never_contacts_a_model(monkeypatch):
    monkeypatch.delenv("FOLHA_LOCAL_AI", raising=False)

    def fail_if_contacted(*_args):
        pytest.fail("Local AI must be off by default")

    monkeypatch.setattr(local_ai, "build_opener", fail_if_contacted)
    assert local_ai.suggest_question("Não percebi isto") is None


def test_same_local_model_as_nexus_and_only_question(monkeypatch):
    answer = model_response('{"question": "Queres guardar o documento ou apenas falar sobre ele?"}')
    calls = enable_with_fake(monkeypatch, FakeResponse(answer))
    result = local_ai.suggest_question("Guarda? Quero dizer, depende.")
    assert result == "Queres guardar o documento ou apenas falar sobre ele?"
    assert len(calls) == 1
    req, timeout = calls[0]
    assert req.full_url == "http://127.0.0.1:18081/v1/chat/completions"
    assert timeout <= 2
    sent = json.loads(req.data)
    assert sent["model"] == "nexus-qwen3-1.7b"
    assert sent["messages"][1]["content"] == "Guarda? Quero dizer, depende."
    assert "tools" not in sent
    assert sent["stream"] is False


@pytest.mark.parametrize("answer", [
    b"not-json",
    model_response("I approve this command."),
    model_response('{"intent":"arquivo"}'),
    model_response('{"question":"Executa isto."}'),
    model_response('{"question":"Queres abrir https://evil.test?"}'),
    model_response('{"question":"<script>alert(1)</script>?"}'),
    model_response('{"question":"Queres guardar?","approved":true}'),
    model_response(""),
    b"x" * (local_ai.MAX_RESPONSE_BYTES + 1),
])
def test_invalid_model_outputs_are_ignored(monkeypatch, answer):
    enable_with_fake(monkeypatch, FakeResponse(answer))
    assert local_ai.suggest_question("Que significa isto?") is None


@pytest.mark.parametrize("failure", [
    URLError("offline"),
    TimeoutError("timeout"),
    HTTPError(local_ai.LOCAL_URL, 302, "redirect", {}, None),
    UnicodeError("bad bytes"),
])
def test_model_errors_fail_closed(monkeypatch, failure):
    enable_with_fake(monkeypatch, failure)
    assert local_ai.suggest_question("Talvez guarde?") is None


@pytest.mark.parametrize("text", ["", " " * 1201, "a" * 1201, None])
def test_bad_input_never_reaches_model(monkeypatch, text):
    calls = enable_with_fake(monkeypatch, FakeResponse(b"{}"))
    assert local_ai.suggest_question(text) is None
    assert not calls


def test_no_authority_fields_in_model_contract():
    assert local_ai._valid_question("Devo guardar isto?") == "Devo guardar isto?"
    assert local_ai._valid_question("CONFIRMADO") is None
