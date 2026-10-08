"""LanguageTool shadow must obey Java UTF-16 positions and Unicode boundaries."""
import pytest
from nexus.adapters.languagetool import correction_shadow
from nexus.contracts import Blocked
from nexus.frontdoor import parse_with_languagetool


def diagnostic(offset, length, replacement):
    return {
        "warnings": {"incompleteResults": False},
        "matches": [{
            "offset": offset,
            "length": length,
            "replacements": [{"value": replacement}],
        }],
    }


@pytest.mark.parametrize("text,offset,length,expected", [
    ("Corige a nota", 0, 6, "Corrige a nota"),
    ("🙂 Corige o livro", 3, 6, "🙂 Corrige o livro"),
    ("👩‍💻 Corige isto", 6, 6, "👩‍💻 Corrige isto"),
    ("á Corige", 3, 6, "á Corrige"),
])
def test_utf16_shadow_with_emoji_and_combining_marks(text, offset, length, expected):
    result = correction_shadow(text, diagnostic(offset, length, "Corrige"))
    assert result == expected
    assert parse_with_languagetool(text, diagnostic(offset, length, "Corrige")).original == text


@pytest.mark.parametrize("offset,length", [
    (1, 1),   # Middle of an emoji surrogate pair
    (0, 1),   # End in middle of emoji
    (30, 2),  # Beyond available text
    (0, 0),
])
def test_surrogate_and_bounds_are_not_accepted(offset, length):
    with pytest.raises(Blocked):
        correction_shadow("🙂 Corige", diagnostic(offset, length, "X"))


def test_never_mutates_original_even_if_corrected_shadow_changes():
    original = "🙂 Corige o texto"
    corrected = parse_with_languagetool(original, diagnostic(3, 6, "Corrige"))
    assert corrected.original == original
    assert corrected.shadow == "🙂 Corrige o texto"
    assert corrected.intent == "trabalhar"
