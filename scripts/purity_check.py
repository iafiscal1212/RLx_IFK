#!/usr/bin/env python3
"""
Purity v2 — incluye verificación de Shield local y sin red en predict/train
"""
import subprocess, sys, os, json, argparse, pathlib, re, hashlib, datetime
BANNED_NET = ["requests","urllib","urllib3","httpx","aiohttp","websocket","websockets","grpc","paramiko","boto3","paho","pika","kafka","pulsar","ftplib","smtplib","imaplib"]
REMOTE_URL = re.compile(r"(?i)\b(?:https?|wss?)://(?!127\.0\.0\.1|localhost)[^\s\"'<>\\\{\}\[\]]+")
REQ = ["data/shield_patterns.yaml"]; OPT = ["data/prompt_fingerprint.model.json"]
SCAN_DIRS=["predict","train", "rlx_sat"]
def run(cmd): p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); return p.returncode,p.stdout
def sha256f(p): import hashlib; h=hashlib.sha256(); f=open(p,"rb");
for chunk in iter(lambda:f.read(1048576), b""): h.update(chunk)
return h.hexdigest()
def read(p):
    try: return open(p,"r",encoding="utf-8",errors="ignore").read()
    except: return ""
def listf(root):
    for dp,_,fn in os.walk(root):
        for f in fn: yield os.path.join(dp,f)
def local_assets():
    rep={"missing":[], "present":[], "model_schema_ok":None, "hashes":{}}
    for rel in REQ:
        if not os.path.exists(rel): rep["missing"].append(rel)
        else: rep["present"].append(rel); rep["hashes"][rel]=sha256f(rel)
    for rel in OPT:
        if os.path.exists(rel):
            rep["present"].append(rel); rep["hashes"][rel]=sha256f(rel)
            try:
                d=json.load(open(rel,"r",encoding="utf-8"))
                rep["model_schema_ok"]= all(k in d for k in ("class_priors","cond","vocab","default"))
            except Exception: rep["model_schema_ok"]=False
    return rep
def no_network_scan():
    f={"files_with_net_libs":[],"files_with_remote_urls":[]}
    for root in [d for d in SCAN_DIRS if os.path.isdir(d)]:
        for p in listf(root):
            if not p.endswith((".py",".rs",".js",".ts",".tsx",".jsx",".sh",".ps1",".yaml",".yml",".json",".md")): continue
            txt=read(p)
            hits=[]
            for lib in BANNED_NET:
                if re.search(rf'(?m)^\s*(from\s+{re.escape(lib)}\s+import|import\s+{re.escape(lib)}\b)|require\(["\']{re.escape(lib)}["\']\)', txt):
                    hits.append(lib)
            if hits: f["files_with_net_libs"].append({"file":p,"libs":sorted(set(hits))})
            urls=[u for u in REMOTE_URL.findall(txt) if "localhost" not in u and "127.0.0.1" not in u]
            if urls: f["files_with_remote_urls"].append({"file":p,"urls":sorted(set(urls))[:10]})
    return f
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--out",default="reports/purity_summary.json"); args=ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    summary={"timestamp_utc":datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z","guards":{},"shield_local_assets":{},"code_no_network":{},"status":"PASS"}
    for name,cmd in [("llm_guard",["python3","scripts/llm_guard.py","--root",args.root,"--out","reports/llm_guard_report.json"]),
                     ("net_guard",["python3","scripts/net_guard.py","--root",args.root,"--out","reports/net_guard_report.json"]),
                     ("secrets_guard",["python3","scripts/secrets_guard.py","--root",args.root,"--out","reports/secrets_guard_report.json"])]:
        rc,out=run(cmd); summary["guards"][name]={"exit_code":rc};
        if rc!=0: summary["status"]="FAIL"
    assets=local_assets(); summary["shield_local_assets"]=assets
    if assets["missing"] or assets.get("model_schema_ok") is False: summary["status"]="FAIL"
    nn=no_network_scan(); summary["code_no_network"]=nn
    if nn["files_with_net_libs"] or nn["files_with_remote_urls"]: summary["status"]="FAIL"
    json.dump(summary, open(args.out,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("[PASS] purity_check OK:", args.out) if summary["status"]=="PASS" else print("[FAIL] purity_check:", args.out)
    sys.exit(0 if summary["status"]=="PASS" else 10)
if __name__=="__main__": main()
