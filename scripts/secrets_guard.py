#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import re
import sys

from scripts.utils import read_file_content

EXTS={".py",".rs",".js",".ts",".tsx",".jsx",".json",".yaml",".yml",".toml",".env",".ini",".cfg",".md",".sh",".ps1"}
API=[
    # Generic keys
    r"\b(api|secret|private)[_-]?key\b",
    r"bearer\s+[a-z0-9\-\._~\+\/]+=*",
    # AI Providers
    r"OPENAI_API_KEY",
    r"ANTHROPIC_API_KEY",
    r"HUGGINGFACE_TOKEN",
    r"COHERE_API_KEY",
    r"GROQ_API_KEY",
    r"MISTRAL_API_KEY",
    # Cloud Providers
    r"AWS_ACCESS_KEY_ID", r"AWS_SECRET_ACCESS_KEY",
    # Common Services
    r"ghp_[0-9a-zA-Z]{36}", # GitHub PAT
    r"xox[pboa]-[0-9]{10,12}-[0-9]{10,12}-[0-9]{10,12}-[a-z0-9]{32}", # Slack
    r"(sk|pk)_(test|live)_[0-9a-zA-Z]{24}", # Stripe
]
CMD = [
    r"\bcurl\s",
    r"\bwget\s",
    r"\biwr\s",
    r"\binvoke-webrequest\b",
    r"\bnc\s",
    r"\bncat\s",
]
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="reports/secrets_guard_report.json")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    api = []
    cmd = []
    # Get the absolute path of this script to avoid self-scanning
    script_path = os.path.realpath(__file__)

    for dp, _, fn in os.walk(args.root):
        for f in fn:
            if pathlib.Path(f).suffix.lower() not in EXTS:
                continue
            p = os.path.join(dp, f)
            # Skip self-scanning
            if os.path.realpath(p) == script_path:
                continue
            txt = read_file_content(p)
            rel = os.path.relpath(p, args.root)
            for pat in API:
                if re.search(pat, txt, flags=re.IGNORECASE):
                    api.append({"file": rel, "pattern": pat})
                    break
            for pat in CMD:
                if re.search(pat, txt, flags=re.IGNORECASE):
                    cmd.append({"file": rel, "pattern": pat})
                    break
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(
            {"api_markers": api, "cmd_suspects": cmd},
            f,
            indent=2,
            ensure_ascii=False
        )
    if api or cmd:
        print("[WARN] Secrets guard")
        sys.exit(4)
    print("[PASS] Secrets guard")
    sys.exit(0)

if __name__ == "__main__":
    main()
