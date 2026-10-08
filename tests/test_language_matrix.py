"""Independent PT-PT language matrix: realistic phrases, typos and safety gates."""
import pytest
from nexus.frontdoor import parse, parse_with_languagetool

CASES = [
 ("Guarda esta nota.", "arquivo"), ("Arquiva o texto.", "arquivo"),
 ("Salva esta informação.", "arquivo"), ("guarda isto", "arquivo"),
 ("Pesquisa na internet o assunto.", "web"), ("Procura na web.", "web"),
 ("Pesquiza online esta expressão.", "web"),
 ("Encontra fontes sobre o tema.", "fontes"), ("Quais são as fontes?", "fontes"),
 ("Dá-me fontes fiáveis.", "fontes"),
 ("Revê o documento.", "trabalhar"), ("Melhora esta frase.", "trabalhar"),
 ("Corrige os erros.", "trabalhar"), ("Reescreve a introdução.", "trabalhar"),
 ("Explica esta passagem.", "perguntar"), ("Como funciona?", "perguntar"),
 ("Quem é o autor?", "perguntar"), ("O que é isto?", "perguntar"),
 ("Calcula 3 + 4.", "calcular"), ("Quanto é 8 vezes 3?", "calcular"),
 ("Soma 5 e 6.", "calcular"), ("Faz uma conta.", "calcular"),
 ("Tema astronomia", "tema"), ("Assunto botânica", "tema"),
 ("Quero falar sobre literatura.", "tema"),
]
UNRESOLVED = [
 "Olá.", "Bom dia.", "Obrigado.", "Faz isso.", "Preciso de ajuda.",
 "Corrige e calcula esta conta.", "Guarda e revê o texto.",
 "Pesquisa na web e arquiva.", "Explica e soma 3 + 4.",
 "Não sei o que fazer.", "O documento está pronto.",
 "O autor disse «guarda isto» no romance.",
 "Isto é uma nota sobre a palavra corrige.",
]
PREFIXES = [("@@","arquivo"),("@","web"),('""',"fontes"),("&","trabalhar"),
 ("??","perguntar"),("%","calcular"),("#","tema")]
@pytest.mark.parametrize("text,intent",CASES)
def test_natural_pt_pt(text,intent):
    x=parse(text)
    assert (x.status,x.intent,x.original)==("RESOLVED",intent,text)

@pytest.mark.parametrize("text",UNRESOLVED)
def test_ambiguous_and_non_command(text):
    x=parse(text)
    assert x.status=="UNRESOLVED", (text,x.as_dict())

@pytest.mark.parametrize("prefix,intent",PREFIXES)
def test_all_explicit_prefixes(prefix,intent):
    text=" \t"+prefix+" conteúdo com acentos áéíóú"
    x=parse(text)
    assert x.status=="RESOLVED" and x.intent==intent and x.original==text and x.explicit

@pytest.mark.parametrize("text",["", "  \n\t", "@@", "??", "#"])
def test_missing_instruction_is_not_executable(text):
    assert parse(text).status=="UNRESOLVED"

@pytest.mark.parametrize("text",["\x00", "\x01executa", "olá\x7f"])
def test_control_chars_do_not_resolve(text):
    x=parse(text)
    assert x.status!="RESOLVED"

@pytest.mark.parametrize("text",["Corrige e calcula.", "Guarda e pesquisa na internet.", "Explica e revê."])
def test_multi_intent_is_not_auto_selected(text):
    x=parse(text)
    assert x.status=="UNRESOLVED" and x.intent is None

def test_correction_shadow_preserves_original():
    original="Corige o texto"
    raw={"warnings":{"incompleteResults":False},"matches":[{"offset":0,"length":6,"replacements":[{"value":"Corrige"}]}]}
    x=parse_with_languagetool(original,raw)
    assert x.original==original and x.shadow=="Corrige o texto" and x.intent=="trabalhar"

def test_incomplete_languagetool_falls_back_to_unresolved():
    x=parse_with_languagetool("Corige",{"warnings":{"incompleteResults":True},"matches":[]})
    assert x.status=="UNRESOLVED" and x.original=="Corige"

@pytest.mark.parametrize("i",range(1000))
def test_original_bytes_semantics_and_prefix_stability(i):
    text=f"  @@ nota {i} — ação \u2603"
    x=parse(text)
    assert x.status=="RESOLVED" and x.intent=="arquivo" and x.original==text
