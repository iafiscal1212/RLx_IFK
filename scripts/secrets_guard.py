#!/usr/bin/env python3
# stdlib-only, sin red
import argparse
import json
import os
import pathlib
import re
import sys
EXTS = {
    ".py",".rs",".js",".ts",".tsx",".jsx",".json",".yaml",".yml",
    ".toml",".env",".ini",".cfg",".md",".sh",".ps1"
}
API_PATTERNS = [
    r"OPENAI_API_KEY", r"ANTHROPIC_API_KEY", r"HUGGINGFACE", r"COHERE_API_KEY",
    r"GROQ_API_KEY", r"MISTRAL_API_KEY", r"\bAPI_KEY\b", r"SECRET_KEY",
    r"BEARER\s+[A-Za-z0-9\-\._~\+\/]+"
]
CMD_PATTERNS = [r"\bcurl\s", r"\bwget\s", r"\biwr\s", r"\binvoke-webrequest\b", r"\bnc\s", r"\bncat\s"]
def read_text(p: str) -> str:
    try:
        return open(p, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="reports/secrets_guard_report.json")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    findings = {"api_markers": [], "cmd_suspects": []}
    for dp, _, fn in os.walk(args.root):
        for name in fn:
            if pathlib.Path(name).suffix.lower() not in EXTS:
                continue
            p = os.path.join(dp, name)
            txt = read_text(p)
            for pat in API_PATTERNS:
                if re.search(pat, txt):
                    findings["api_markers"].append({"file": p, "pattern": pat})
                    break
            for pat in CMD_PATTERNS:
                if re.search(pat, txt, flags=re.IGNORECASE):
                    findings["cmd_suspects"].append({"file": p, "pattern": pat})
                    break
    json.dump(findings, open(args.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    fail = bool(findings["api_markers"] or findings["cmd_suspects"])
    if fail:
        print("[WARN] Secrets guard: posibles claves/comandos detectados")
        sys.exit(4)
    print("[PASS] Secrets guard limpio.")
    sys.exit(0)
if __name__ == "__main__":
    main()
