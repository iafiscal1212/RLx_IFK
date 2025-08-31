import re
import yaml
from functools import lru_cache
from pathlib import Path

I18N_DIR = Path(__file__).parent.parent / "i18n"

def _iter_terms(glossary: dict):
    """Admite formatos simple {'a':'b'} y avanzado {'a':{'target':'b','variations':[...]}}."""
    terms = []
    if not isinstance(glossary, dict):
        return terms
    for base, val in glossary.items():
        if isinstance(val, str):
            terms.append((base, val))
        elif isinstance(val, dict) and "target" in val:
            tgt = val.get("target", "")
            forms = [base] + list(val.get("variations", []))
            for f in forms:
                terms.append((f, tgt))
    terms.sort(key=lambda kv: len(kv[0]), reverse=True)
    return terms

@lru_cache(maxsize=128)
def _compile_glossary(items_tuple):
    pats = []
    for term, repl in items_tuple:
        pat = re.compile(r"\b" + re.escape(term) + r"\b", flags=re.IGNORECASE | re.UNICODE)
        pats.append((pat, repl))
    return pats

def _apply_glossary(text: str, glossary: dict) -> str:
    if not glossary:
        return text
    items = tuple(_iter_terms(glossary))
    out = text
    for pat, repl in _compile_glossary(items):
        out = pat.sub(repl, out)
    return out

def localize(structure: dict, target_lang: str, glossary: dict | None = None) -> dict:
    """Localiza microcopy y aplica glosario de dominio; no toca el texto original salvo términos del glosario."""
    strings = {}
    strings_path = I18N_DIR / "strings" / f"{target_lang}.yaml"
    if strings_path.exists():
        try:
            with open(strings_path, "r", encoding="utf-8") as f:
                strings = yaml.safe_load(f) or {}
        except Exception:
            strings = {}

    bullets = [_apply_glossary(b, glossary or {}) for b in structure.get("bullets", [])]
    opts    = [_apply_glossary(o, glossary or {}) for o in structure.get("options", [])]

    return {
        "headers": {
            "summary": strings.get("summary", "Summary"),
            "options": (strings.get("options", "Options ({count})")).format(count=len(opts)),
        },
        "bullets": bullets,
        "options": opts,
        "alerts": structure.get("alerts", []),
        "kpis": {
            "friction": (strings.get("friction", "Friction: {value:.2f}")).format(value=0.0),
            "hick": (strings.get("hick", "Hick efficiency: {value:.2f}")).format(value=1.0),
            "ttc": " ",
        },
    }
