"""Diverse bidirectional inputs; deterministic safety and round-trip gates."""
import itertools
import pytest
from nexus.frontdoor import parse

PREFIXES = {"@@":"arquivo","@":"web",'""':"fontes","&":"trabalhar",
            "??":"perguntar","%":"calcular","#":"tema"}
SUBJECTS = [
    "um livro", "uma carta", "o relatório", "a nota", "o artigo", "a tabela",
    "a história", "um poema", "o projeto", "o capítulo", "a receita",
    "o diário", "um orçamento", "a investigação", "um resumo", "a biografia",
    "o documento", "o índice", "uma legenda", "a bibliografia",
]
MODIFIERS = [
    "com cuidado", "sem perder detalhes", "em português europeu",
    "com referências", "de forma clara", "com acentos áéíóú",
    "com o emoji ☃", "para amanhã", "com rigor", "sem pressa",
]
FORMATS = ["{}: {} — {}", "{} {} ({})", "  {}\t{}; {}", "{}\n{}\n{}"]
CASES = [
    (prefix, intent, subject, modifier, template)
    for (prefix, intent), subject, modifier, template
    in itertools.product(PREFIXES.items(), SUBJECTS, MODIFIERS, FORMATS)
]

@pytest.mark.parametrize("prefix,intent,subject,modifier,template", CASES)
def test_5600_diverse_explicit_roundtrips(prefix, intent, subject, modifier, template):
    original = template.format(prefix, subject, modifier)
    result = parse(original)
    assert result.status == "RESOLVED"
    assert result.intent == intent
    assert result.explicit is True
    assert result.original == original
    assert result.content.strip()
    assert result.as_dict()["original"].encode("utf-8") == original.encode("utf-8")

@pytest.mark.parametrize("text", [
    "", "  ", "\n\t", "Olá.", "Bom dia.", "Obrigado.", "Faz isso.",
    "Guarda e calcula.", "Corrige e calcula.", "Pesquisa na web e arquiva.",
    "O autor disse «guarda isto» no romance.",
    'A frase "corrige isto" está no livro.',
    "Não quero que guardes isto.", "Nunca calcules esta conta.",
])
def test_ambiguous_inputs_never_authorize(text):
    result = parse(text)
    assert result.status != "RESOLVED"
    assert "execute" not in result.as_dict()
    assert "approved" not in result.as_dict()
