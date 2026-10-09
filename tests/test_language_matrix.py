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

@pytest.mark.parametrize("text",[
    "Não quero que guardes isto.",
    "Nunca calcules esta conta.",
    "O autor disse «guarda isto» no romance.",
    'A frase "corrige isto" está no livro.',
])
def test_quoted_or_negated_commands_require_clarification(text):
    result=parse(text)
    assert result.status=="UNRESOLVED" and result.intent is None

def test_intent_is_not_permission():
    result=parse("Corrige este texto.")
    assert result.status=="RESOLVED"
    assert "approved" not in result.as_dict()
    assert "execute" not in result.as_dict()

@pytest.mark.parametrize("phrase", [
    "Não quero guardar esta nota.",
    "Nao quero guardar esta nota.",
    "Nunca guardar isto.",
    "Não guarda este texto.",
    "Não quero que guardes isto.",
    "Não arquiva o relatório.",
    "Não quero corrigir isto.",
    "Não corrige a frase.",
    "Não quero calcular a conta.",
    "Não calcula os valores.",
    "Não quero pesquisar na web.",
    "Não pesquisa na internet.",
    "Não quero explicar o assunto.",
    "Isto é uma nota sobre a palavra corrige.",
    "O título contém a frase «guarda isto».",
])
def test_negation_and_mentions_are_not_commands(phrase):
    result = parse(phrase)
    assert result.status == "UNRESOLVED", (phrase, result.as_dict())
    assert result.intent is None


@pytest.mark.parametrize("phrase", [
    "Evita guardar esta nota.",
    "Quero evitar guardar este ficheiro.",
    "Sem guardar o documento, continua.",
    "Proíbo guardar o meu texto.",
    "Deixa de guardar as minhas notas.",
])
def test_negative_archive_phrases_never_become_positive_proposals(phrase):
    """A negated archival reference is not an archive request."""
    result = parse(phrase)
    assert result.status == "UNRESOLVED", (phrase, result.as_dict())
    assert result.intent is None


@pytest.mark.parametrize("phrase", [
    "@@\x7f",
    "Guarda\x7f isto.",
    "&\x7f executar",
])
def test_ascii_delete_character_never_forms_a_valid_proposal(phrase):
    """DEL is a non-printable ASCII control, including in explicit requests."""
    result = parse(phrase)
    assert result.status == "BLOCKED", (phrase, result.as_dict())
    assert result.intent is None
    assert result.original == phrase
