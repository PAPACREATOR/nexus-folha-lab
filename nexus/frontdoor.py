"""Minimal deterministic Front Door: data-driven rules, no authority."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from nexus.contracts import ROOT, Blocked, strict_json, validate
from nexus.adapters.languagetool import correction_shadow


_RULES = validate("frontdoor_rules", strict_json((ROOT / "frontdoor_rules.json").read_bytes()))
PREFIXES = tuple((item[0], item[1]) for item in _RULES["prefixes"])
NATURAL_RULES = _RULES["natural_rules"]
MAX_TEXT_CHARS = _RULES["max_text_chars"]


@dataclass(frozen=True)
class ParsedInput:
    status: str
    intent: str | None
    original: str
    content: str
    parser: str
    explicit: bool
    shadow: str | None = None

    def as_dict(self) -> dict:
        value = {
            "status": self.status,
            "intent": self.intent,
            "original": self.original,
            "content": self.content,
            "parser": self.parser,
            "explicit": self.explicit,
        }
        if self.shadow is not None:
            value["shadow"] = self.shadow
        return value


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def _natural(text: str, *, original: str | None = None, parser="eliza-rules-v1",
             shadow: str | None = None) -> ParsedInput:
    normal = _normalise(text)
    matches = [
        intent for intent, patterns in NATURAL_RULES.items()
        if any(re.search(pattern, normal) for pattern in patterns)
    ]
    source = text if original is None else original
    if len(matches) != 1:
        return ParsedInput("UNRESOLVED", None, source, source, parser, False, shadow)
    # Quoted instructions and explicit negations must not be silently executed.
    if re.search(r'\b(?:não|nao|nunca|jamais)(?:\s+\w+){0,3}\s+(?:guarda(?:r|s|es)?|arquiva(?:r|s|es)?|salva(?:r|s|es)?|corrige(?:r|s)?|revê|reve|rever|melhora(?:r|s)?|calcula(?:r|s|es)?|soma(?:r|s|es)?|pesquisa(?:r|s|es)?|procura(?:r|s|es)?|reescreve(?:r|s)?|explica(?:r|s)?)\b', normal):
        return ParsedInput("UNRESOLVED", None, source, source, parser, False, shadow)
    if re.search(r'[«“"][^»”"]*(?:guarda|corrige|calcula|pesquisa|arquiva)[^»”"]*[»”"]', text, re.IGNORECASE):
        return ParsedInput("UNRESOLVED", None, source, source, parser, False, shadow)
    if re.search(r"\b(?:a palavra|a frase|o termo)\s+(?:guarda|corrige|calcula|pesquisa|arquiva)\b", normal):
        return ParsedInput("UNRESOLVED", None, source, source, parser, False, shadow)
    return ParsedInput("RESOLVED", matches[0], source, source, parser, False, shadow)


def parse_explicit(text: str) -> ParsedInput:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if len(text) > MAX_TEXT_CHARS or any(ord(c) < 32 and c not in "\t\n\r" for c in text):
        return ParsedInput("BLOCKED", None, text, "", "prefix-v1", False)
    if not text.strip():
        return ParsedInput("UNRESOLVED", None, text, "", "prefix-v1", False)

    candidate = text.lstrip()
    for prefix, intent in PREFIXES:
        if candidate.startswith(prefix):
            content = candidate[len(prefix):].lstrip()
            return ParsedInput(
                "RESOLVED" if content else "UNRESOLVED",
                intent,
                text,
                content,
                "prefix-v1",
                True,
            )
    return ParsedInput("UNRESOLVED", None, text, text, "prefix-v1", False)


def parse(text: str) -> ParsedInput:
    explicit = parse_explicit(text)
    if explicit.status != "UNRESOLVED" or explicit.explicit:
        return explicit
    return _natural(text)


def parse_with_languagetool(text: str, raw) -> ParsedInput:
    first = parse(text)
    if first.status != "UNRESOLVED" or first.explicit:
        return first
    try:
        shadow = correction_shadow(text, raw)
    except (Blocked, TypeError, ValueError, KeyError):
        return first
    if shadow == text:
        return first
    return _natural(
        shadow,
        original=text,
        parser="languagetool-shadow+eliza-v1",
        shadow=shadow,
    )
