"""Optional localhost-only LanguageTool diagnostics, used for interpretation only.

No process launch, no cloud fallback, no changes to original user text.
The existing Nexus Windows LanguageTool CLI is not modified or replaced.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

LOCAL_LT_URL = "http://127.0.0.1:8081/v2/check"
MAX_LT_TEXT = 1200
MAX_LT_JSON = 128_000


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def local_diagnostic(text: str) -> dict | None:
    """Fetch a spelling diagnostic only if deterministic interpretation failed."""
    if os.environ.get("FOLHA_LOCAL_LT") != "1":
        return None
    if not isinstance(text, str) or not 1 <= len(text) <= MAX_LT_TEXT:
        return None
    payload = urlencode({"language": "pt-PT", "text": text}).encode("utf-8")
    request = Request(
        LOCAL_LT_URL, data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=1.5) as response:
            if response.status != 200:
                return None
            body = response.read(MAX_LT_JSON + 1)
        if len(body) > MAX_LT_JSON:
            return None
        value = json.loads(body.decode("utf-8"))
        if not isinstance(value, dict):
            return None
        if not isinstance(value.get("warnings"), dict):
            return None
        if value["warnings"].get("incompleteResults") is not False:
            return None
        if not isinstance(value.get("matches"), list):
            return None
        return value
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, TypeError,
            UnicodeError):
        return None
