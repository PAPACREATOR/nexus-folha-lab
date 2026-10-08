import pytest
from nexus.frontdoor import parse, parse_with_languagetool
from nexus.adapters.languagetool import correction_shadow
from nexus.contracts import Blocked

def test_explicit_and_original():
    text="  @@ guarda isto"
    x=parse(text)
    assert x.status=="RESOLVED" and x.intent=="arquivo" and x.original==text

def test_natural():
    x=parse("Corrige este texto.")
    assert x.status=="RESOLVED" and x.intent=="trabalhar"

def test_ambiguous_never_executes():
    x=parse("Corrige e calcula esta conta.")
    assert x.status=="UNRESOLVED" and x.intent is None

def test_language_tool_shadow():
    text="Corige este texto"
    raw={"warnings":{"incompleteResults":False},"matches":[{"offset":0,"length":6,"replacements":[{"value":"Corrige"}]}]}
    x=parse_with_languagetool(text,raw)
    assert x.status=="RESOLVED" and x.intent=="trabalhar" and x.original==text and x.shadow=="Corrige este texto"

def test_incomplete_rejected():
    with pytest.raises(Blocked): correction_shadow("texto",{"warnings":{"incompleteResults":True},"matches":[]})

def test_many_unicode_originals():
    for n in range(1000):
        text=f"@@ nota número {n} — ação"
        x=parse(text)
        assert x.original==text and x.intent=="arquivo"
