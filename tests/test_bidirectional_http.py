"""End-to-end HTTP contract tests; never execute real actions."""
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from folha_lab.server import Handler

def test_http_bidirectional_proposal_and_ambiguity():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/", timeout=5) as response:
            page = response.read().decode("utf-8")
            assert "<textarea" in page and "Interpretar" in page
            assert 'id="confirm"' in page and 'id="reject"' in page
            assert 'field.addEventListener("input"' in page
            assert "Nenhuma ação foi executada." in page
        for phrase, expected in [
            ("Guarda esta nota", "RESOLVED"),
            ("Corrige o texto", "RESOLVED"),
            ("Olá", "UNRESOLVED"),
            ("Guarda e calcula", "UNRESOLVED"),
            ("Não quero que guardes isto", "UNRESOLVED"),
        ]:
            req = Request(base + "/interpret", data=json.dumps({"text": phrase}).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=5) as response:
                result = json.load(response)
            assert result["status"] == expected, (phrase, result)
            assert result["original"] == phrase
            assert result["execution"] == "SIMULATED_ONLY"
            assert result["confirmation_required"] is (expected == "RESOLVED")
            if expected == "RESOLVED":
                assert result["proposal_id"] and result["question"]
            else:
                assert result["question"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
