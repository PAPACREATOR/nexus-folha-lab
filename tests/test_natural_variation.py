"""Thousands of natural PT-PT requests across intents, polite forms and contexts.

No numeric-only substitutions: every expected intent is independently fixed.
"""
import itertools
import pytest
from nexus.frontdoor import parse

TOPICS = (
    "a bicicleta", "o caderno", "a fotografia", "o poema",
    "a cadeira", "o algoritmo", "a notícia", "a receita",
    "o livro", "um artigo", "a imagem", "o programa",
    "a atividade", "a montanha", "o mapa", "a entrevista",
)
NUMBERS = (
    "7 e 3", "12 e 8", "20 e 5", "9 e 4", "100 e 2",
    "3 e 3", "14 e 6", "11 e 9", "30 e 12", "40 e 10",
    "72 e 8", "45 e 5", "66 e 6", "25 e 4", "5 e 1", "2 e 2",
)
TEMPLATES = {
    "arquivo": (
        "Guarda {}", "Arquiva {}", "Salva {}",
        "Quero guardar {}", "Podes guardar {}", "Preciso de arquivar {}",
    ),
    "web": (
        "Pesquisa na internet {}", "Procura na web {}", "Pesquiza online {}",
        "Pesquisa online {}", "Quero pesquisar na web {}", "Podes procurar na internet {}",
    ),
    "fontes": (
        "Encontra fontes para {}", "Quais são as fontes de {}", "Dá-me fontes sobre {}",
        "Procura fontes para {}", "Pesquisa fontes acerca de {}", "Quais as fontes sobre {}",
    ),
    "trabalhar": (
        "Corrige {}", "Revê {}", "Melhora {}",
        "Reescreve {}", "Quero rever {}", "Preciso de melhorar {}",
    ),
    "perguntar": (
        "Explica {}", "Como funciona {}", "O que é {}",
        "Quem é o autor de {}", "Podes explicar {}", "Responde sobre {}",
    ),
    "calcular": (
        "Calcula {}", "Quanto é {}", "Soma {}",
        "Faz uma conta com {}", "Podes calcular {}", "Quero somar {}",
    ),
    "tema": (
        "Tema {}", "Assunto {}", "Quero falar sobre {}",
        "Tema: {}", "Assunto: {}", "Quero falar sobre: {}",
    ),
}
INTRO = ("", "Por favor, ", "Se puderes, ")
OUTRO = ("", " agora.", " com cuidado.", " para mim.")
CASES = tuple(
    (intent, intro + template.format(topic) + outro)
    for intent, templates in TEMPLATES.items()
    for template, topic, intro, outro in itertools.product(
        templates, NUMBERS if intent == "calcular" else TOPICS,
        ("",) if intent == "tema" else INTRO, OUTRO
    )
)

@pytest.mark.parametrize("intent,phrase", CASES)
def test_7296_natural_variants(intent, phrase):
    result = parse(phrase)
    assert result.status == "RESOLVED", (phrase, result.as_dict())
    assert result.intent == intent, (phrase, result.as_dict())
    assert result.original == phrase
    assert result.explicit is False
    assert result.as_dict()["original"].encode("utf-8") == phrase.encode("utf-8")
