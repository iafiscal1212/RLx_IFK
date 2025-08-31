#!/usr/bin/env bash
set -euo pipefail

write() { mkdir -p "$(dirname "$1")"; cat > "$1" <<'EOF'
'"$2"'
EOF
echo "[OK] $1"; }

# 1) Purity check — versión ruff-friendly + SCAN_DIRS completo
write scripts/purity_check.py "$(cat <<'PY'
#!/usr/bin/env python3
# stdlib-only, sin red
import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

REMOTE_URL = re.compile(
    r"(?i)\b(?:https?|wss?)://(?!127\.0\.0\.1|localhost)[^\s\"'<>\\\{\\}\[\]]+"
)

REQ = ["data/shield_patterns.yaml"]
OPT = ["data/prompt_fingerprint.model.json"]

# carpetas a escanear: no abrir sockets ni contener URLs remotas
SCAN_DIRS = [
    "app",
    "companion",
    "i18n",
    "predict",
    "profiles",
    "renderer",
    "rlx_backend",
    "tuner",
    "train",
    "tools",
    "rlx_sat",
]

def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout

def list_files(root: str):
    for dp, _, fn in os.walk(root):
        for name in fn:
            yield os.path.join(dp, name)

def local_assets_check() -> dict:
    rep = {"missing": [], "present": [], "model_schema_ok": None, "hashes": {}}
    import hashlib
    def sha256f(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    for rel in REQ:
        if not os.path.exists(rel):
            rep["missing"].append(rel)
        else:
            rep["present"].append(rel)
            rep["hashes"][rel] = sha256f(rel)
    for rel in OPT:
        if os.path.exists(rel):
            rep["present"].append(rel)
            rep["hashes"][rel] = sha256f(rel)
            try:
                d = json.load(open(rel, "r", encoding="utf-8"))
                rep["model_schema_ok"] = all(k in d for k in ("class_priors", "cond", "vocab", "default"))
            except Exception:
                rep["model_schema_ok"] = False
    return rep

def scan_no_network_in_code(root: str) -> dict:
    findings = {"files_with_net_libs": [], "files_with_remote_urls": []}
    net_libs = [
        "requests", "urllib", "urllib3", "httpx", "aiohttp", "websocket", "websockets",
        "grpc", "paramiko", "boto3", "paho", "pika", "kafka", "pulsar", "ftplib", "smtplib", "imaplib",
    ]
    for d in SCAN_DIRS:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for p in list_files(base):
            if not p.endswith((".py", ".rs", ".js", ".ts", ".tsx", ".jsx", ".sh", ".ps1", ".yaml", ".yml", ".json", ".md")):
                continue
            try:
                txt = open(p, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            # imports de red
            hits = []
            for lib in net_libs:
                pat1 = rf"(?m)^\s*from\s+{re.escape(lib)}\s+import\s+"
                pat2 = rf"(?m)^\s*import\s+{re.escape(lib)}\b"
                pat3 = rf'require\(["\']{re.escape(lib)}["\']\)'
                if re.search(pat1, txt) or re.search(pat2, txt) or re.search(pat3, txt):
                    hits.append(lib)
            if hits:
                findings["files_with_net_libs"].append({"file": p, "libs": sorted(set(hits))})
            # URLs remotas
            urls = [u for u in REMOTE_URL.findall(txt) if "localhost" not in u and "127.0.0.1" not in u]
            if urls:
                findings["files_with_remote_urls"].append({"file": p, "urls": sorted(set(urls))[:10]})
    return findings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="reports/purity_summary.json")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    summary = {
        "timestamp_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "guards": {},
        "shield_local_assets": {},
        "code_no_network": {},
        "status": "PASS",
    }

    rc, out = run([sys.executable, "scripts/llm_guard.py", "--root", args.root, "--out", "reports/llm_guard_report.json"])
    summary["guards"]["llm_guard"] = {"exit_code": rc}
    if rc != 0:
        summary["status"] = "FAIL"

    rc, out = run([sys.executable, "scripts/net_guard.py", "--root", args.root, "--out", "reports/net_guard_report.json"])
    summary["guards"]["net_guard"] = {"exit_code": rc}
    if rc != 0:
        summary["status"] = "FAIL"

    rc, out = run([sys.executable, "scripts/secrets_guard.py", "--root", args.root, "--out", "reports/secrets_guard_report.json"])
    summary["guards"]["secrets_guard"] = {"exit_code": rc}
    if rc != 0:
        summary["status"] = "FAIL"

    assets = local_assets_check()
    summary["shield_local_assets"] = assets
    if assets["missing"] or assets.get("model_schema_ok") is False:
        summary["status"] = "FAIL"

    nn = scan_no_network_in_code(args.root)
    summary["code_no_network"] = nn
    if nn["files_with_net_libs"] or nn["files_with_remote_urls"]:
        summary["status"] = "FAIL"

    json.dump(summary, open(args.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("[PASS] purity_check OK:", args.out) if summary["status"] == "PASS" else print("[FAIL] purity_check:", args.out)
    sys.exit(0 if summary["status"] == "PASS" else 10)

if __name__ == "__main__":
    main()
PY
)"

# 2) Renderer — apply_glossary robusto + localize limpio (Unicode, cache)
write renderer/localize.py "$(cat <<'PY'
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
PY
)"

# 3) Analyzer v0 (mínimo) — para que el test pase sin LLMs
write app/services/analyzer.py "$(cat <<'PY'
import math
from datetime import datetime

ELONG_MIN = 3
TAU_GAP_S = 300.0

def _gap_factor(last_ts: datetime | None, ts: datetime) -> float:
    if not last_ts:
        return 0.0
    dt = (ts - last_ts).total_seconds()
    return math.exp(-dt / TAU_GAP_S)

def calculate_raw_signals(text: str) -> dict:
    letters = [c for c in text if c.isalpha()]
    n_letters = max(len(letters), 1)
    raw_arousal = (text.count("!") + text.count("?")) / max(len(text), 1)
    raw_caps = sum(1 for c in letters if c.isupper()) / n_letters
    raw_elong = sum(1 for w in text.split() if len(set(w)) < len(w) and any(w.count(ch) >= ELONG_MIN for ch in set(w))) / max(len(text.split()), 1)
    return {"raw_arousal": raw_arousal, "raw_caps": raw_caps, "raw_elong": raw_elong}

def calculate_emotional_load(a_z: float, v_z: float, u_z: float) -> float:
    x = 0.5 * a_z - 0.3 * v_z + 0.2 * u_z
    return 1.0 / (1.0 + math.exp(-x))
PY
)"

# 4) (Opcional) borrado de httpx del requirements para máxima pureza ZTL
if [ -f requirements.txt ]; then
  sed -i '/^httpx\s*$/d' requirements.txt || true
fi

echo
echo "Listo. Ejecuta:"
echo "  python3 scripts/purity_check.py --root ."
echo "  pytest -q  (si tienes tests activos)"
