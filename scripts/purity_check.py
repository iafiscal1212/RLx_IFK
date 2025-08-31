#!/usr/bin/env python3
"""
Purity v2 — incluye verificación de Shield local y sin red en predict/train
"""
import subprocess, sys, os, json, argparse, pathlib, re, hashlib, datetime
from scripts.utils import read_file_content

BANNED_NET = [
    "requests",
    "urllib",
    "urllib3",
    "httpx",
    "aiohttp",
    "websocket",
    "websockets",
    "grpc",
    "paramiko",
    "boto3",
    "paho",
    "pika",
    "kafka",
    "pulsar",
    "ftplib",
    "smtplib",
    "imaplib",
]
REMOTE_URL = re.compile(r"(?i)\b(?:https?|wss?)://(?!127\.0\.0\.1|localhost)[^\s\"'<>\\\{\}\[\]]+")
REQ = ["data/shield_patterns.yaml"]
OPT = ["data/prompt_fingerprint.model.json"]
SCAN_DIRS = [
    "app",
    "companion",
    "i18n",
    "predict",
    "profiles",
    "renderer",
    "rlx_backend",
    "tuner",
]
def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout
def sha256f(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()
def listf(root):
    for dp, _, fn in os.walk(root):
        for f in fn:
            yield os.path.join(dp, f)
def local_assets():
    rep = {"missing": [], "present": [], "model_schema_ok": None, "hashes": {}}
    for path in REQ:
        if not os.path.exists(path):
            rep["missing"].append(path)
        else:
            rep["present"].append(path)
            rep["hashes"][path] = sha256f(path)
    for path in OPT:
        if os.path.exists(path):
            rep["present"].append(path)
            rep["hashes"][path] = sha256f(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                rep["model_schema_ok"] = all(k in d for k in ("class_priors", "cond", "vocab", "default"))
            except (json.JSONDecodeError, TypeError): rep["model_schema_ok"]=False
    return rep
def no_network_scan():
    report = {"files_with_net_libs": [], "files_with_remote_urls": []}
    for root in [d for d in SCAN_DIRS if os.path.isdir(d)]:
        for filepath in listf(root):
            if not filepath.endswith((".py",".rs",".js",".ts",".tsx",".jsx",".sh",".ps1",".yaml",".yml",".json",".md")):
                continue
            txt = read_file_content(filepath)
            hits = []
            for lib in BANNED_NET:
                if re.search(rf'(?m)^\s*(from\s+{re.escape(lib)}\s+import|import\s+{re.escape(lib)}\b)|require\(["\']{re.escape(lib)}["\']\)', txt):
                    hits.append(lib)
            if hits:
                report["files_with_net_libs"].append({"file": filepath, "libs": sorted(set(hits))})
            urls = REMOTE_URL.findall(txt)
            if urls:
                report["files_with_remote_urls"].append({
                    "file": filepath,
                    "urls": sorted(set(urls))[:10]
                })
    return report
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
        "status": "PASS"
    }
    guards_to_run = [
        (
            "llm_guard",
            [
                "python3", "scripts/llm_guard.py", "--root", args.root,
                "--out", "reports/llm_guard_report.json"
            ],
        ),
        (
            "net_guard",
            [
                "python3", "scripts/net_guard.py", "--root", args.root,
                "--out", "reports/net_guard_report.json"
            ],
        ),
        (
            "secrets_guard",
            [
                "python3",
                "scripts/secrets_guard.py",
                "--root",
                args.root,
                "--out",
                "reports/secrets_guard_report.json",
            ],
        ),
    ]
    for name, cmd in guards_to_run:
        rc, out = run(cmd)
        summary["guards"][name] = {"exit_code": rc}
        if rc != 0:
            summary["status"] = "FAIL"

    assets = local_assets()
    summary["shield_local_assets"] = assets
    if assets["missing"] or assets.get("model_schema_ok") is False:
        summary["status"] = "FAIL"

    nn = no_network_scan()
    summary["code_no_network"] = nn
    if nn["files_with_net_libs"] or nn["files_with_remote_urls"]:
        summary["status"] = "FAIL"

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if summary["status"] == "PASS":
        print("[PASS] purity_check OK:", args.out)
        sys.exit(0)
    else:
        print("[FAIL] purity_check:", args.out)
        sys.exit(10)

if __name__ == "__main__":
    main()
