"""Minimal, isolated schema boundary extracted from the historic Nexus contracts."""
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT = Path(__file__).resolve().parent
class Blocked(ValueError):
    pass
def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise Blocked("Campo JSON repetido.")
            result[key] = value
        return result
    def constant(_): raise Blocked("Número JSON inválido.")
    def finite_number(text):
        value = float(text)
        if not math.isfinite(value): raise Blocked("Número JSON fora do limite.")
        return value
    try: return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_number)
    except (ValueError, UnicodeError, RecursionError) as error: raise Blocked("JSON inválido.") from error
def validate(name, value):
    schema = strict_json((ROOT / "schemas" / (name + ".json")).read_bytes())
    if next(Draft202012Validator(schema).iter_errors(value), None): raise Blocked("Contrato inválido: " + name)
    return value
