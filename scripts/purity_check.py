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
