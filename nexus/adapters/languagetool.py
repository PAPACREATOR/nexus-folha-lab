"""Non-authoritative correction shadow, extracted from historic LanguageTool adapter.
No Java subprocess, no external service and no automatic edits to the original.
"""
from nexus.contracts import Blocked, strict_json

def correction_shadow(text, raw):
    value = strict_json(raw) if isinstance(raw, (str, bytes, bytearray)) else raw
    if not isinstance(value, dict) or not isinstance(value.get("warnings"), dict) or not isinstance(value.get("matches"), list):
        raise Blocked("Diagnóstico LanguageTool inválido.")
    if value["warnings"].get("incompleteResults") is not False: raise Blocked("Resultados incompletos.")
    # LanguageTool reports offsets in UTF-16 code units, not Python code points.
    # Only exact Unicode character boundaries may be edited.
    units = 0
    boundaries = {0: 0}
    for index, char in enumerate(text, 1):
        units += 2 if ord(char) > 0xFFFF else 1
        boundaries[units] = index
    edits = []
    for match in value["matches"]:
        if not isinstance(match, dict): raise Blocked("Match inválido.")
        offset, length = match.get("offset"), match.get("length")
        replacements = match.get("replacements", [])
        if not isinstance(offset, int) or isinstance(offset, bool) or not isinstance(length, int) or isinstance(length, bool): continue
        if offset < 0 or length <= 0 or offset + length > units: raise Blocked("Posições inválidas.")
        if offset not in boundaries or offset + length not in boundaries: raise Blocked("Offset dentro de carácter Unicode.")
        if not isinstance(replacements, list) or len(replacements) != 1: continue
        replacement = replacements[0].get("value") if isinstance(replacements[0], dict) else None
        if not isinstance(replacement, str) or len(replacement) > 200 or any(ord(ch) < 32 for ch in replacement): continue
        edits.append((boundaries[offset], boundaries[offset + length], replacement))
    edits.sort()
    if any(b[0] < a[1] for a,b in zip(edits,edits[1:])): raise Blocked("Correções sobrepostas.")
    shadow = text
    for start,end,replacement in reversed(edits): shadow = shadow[:start] + replacement + shadow[end:]
    return shadow
