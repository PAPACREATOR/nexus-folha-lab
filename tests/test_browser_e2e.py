"""Real Chromium E2E gates for the human-facing Folha.

The ordinary pytest matrix skips these if Playwright is not installed;
the dedicated GitHub Actions browser job installs Chromium and must run them.
"""
import threading
from http.server import ThreadingHTTPServer

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright

from folha_lab.server import Handler


@pytest.fixture(scope="module")
def page_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="module")
def chromium():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture()
def page(chromium, page_url):
    context = chromium.new_context(locale="pt-PT")
    tab = context.new_page()
    tab.goto(page_url)
    try:
        yield tab
    finally:
        context.close()


def test_confirm_is_explicit_and_not_execution(page):
    endpoints = []
    page.on("request", lambda req: endpoints.append(req.url))
    page.locator("#text").fill("Guarda este documento.")
    page.locator("#send").click()
    page.locator("#decision").wait_for(state="visible")
    assert "arquivo" in page.locator("#proposal").inner_text()
    assert "Aguardo" in page.locator("#result").inner_text()
    page.locator("#confirm").click()
    assert page.locator("#decision").is_hidden()
    assert "confirmada pelo humano" in page.locator("#result").inner_text()
    assert "Nenhuma ação foi executada" in page.locator("#result").inner_text()
    assert all(
        url.endswith("/") or url.endswith("/interpret") for url in endpoints
    ), endpoints


def test_reject_and_reformulate(page):
    page.locator("#text").fill("Corrige esta frase.")
    page.locator("#send").click()
    page.locator("#decision").wait_for(state="visible")
    page.locator("#reject").click()
    assert page.locator("#decision").is_hidden()
    assert "rejeitada" in page.locator("#result").inner_text().lower()
    page.locator("#text").fill("Calcula 2 mais 2.")
    page.locator("#send").click()
    page.locator("#decision").wait_for(state="visible")
    assert "calcular" in page.locator("#proposal").inner_text()


def test_change_of_text_revokes_stale_proposal(page):
    page.locator("#text").fill("Guarda isto.")
    page.locator("#send").click()
    page.locator("#decision").wait_for(state="visible")
    page.locator("#text").fill("Quero falar sobre História")
    assert page.locator("#decision").is_hidden()
    assert "mudou" in page.locator("#result").inner_text().lower()


@pytest.mark.parametrize("phrase", [
    "Olá.",
    "Guarda e corrige isto.",
    "Não quero guardar a nota.",
    'O autor escreveu «guarda isto» no romance.',
])
def test_ambiguous_text_never_shows_confirmation(page, phrase):
    page.locator("#text").fill(phrase)
    page.locator("#send").click()
    page.wait_for_function(
        "() => !document.getElementById('send').disabled"
    )
    assert page.locator("#decision").is_hidden()
    assert "explicar" in page.locator("#result").inner_text().lower()


def test_untrusted_html_remains_text_not_markup(page):
    page.locator("#text").fill('@@ <img src=x onerror="alert(1)">')
    page.locator("#send").click()
    page.locator("#decision").wait_for(state="visible")
    assert page.locator("img").count() == 0
    page.locator("#confirm").click()
    assert page.locator("img").count() == 0
