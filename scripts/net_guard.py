#!/usr/bin/env python3
import sys, os, re, json, argparse, pathlib
LIBS=["requests","urllib","urllib3","httpx","aiohttp","websocket","websockets","grpc","paramiko","boto3","paho","pika","kafka","pulsar","ftplib","smtplib","imaplib"]
EXTS={".py",".rs",".js",".ts",".tsx",".jsx",".json",".yaml",".yml",".toml",".md",".sh",".ps1"}
URL=re.compile(r"(?i)\b(?:https?|wss?)://(?!127\.0\.0\.1|localhost)[^\s\"'<>\\\{\}\[\]]+")
def read(p):
    try: return open(p,"r",encoding="utf-8",errors="ignore").read()
    except: return ""
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--out",default="reports/net_guard_report.json"); args=ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    imports=[]; endpoints=[]
    for dp,_,fn in os.walk(args.root):
        for f in fn:
            if pathlib.Path(f).suffix.lower() not in EXTS: continue
            p=os.path.join(dp,f); txt=read(p); rel=os.path.relpath(p,args.root)
            hits=[];
            for lib in LIBS:
                if re.search(rf'(?m)^\s*(from\s+{re.escape(lib)}\s+import|import\s+{re.escape(lib)}\b)|require\(["\']{re.escape(lib)}["\']\)', txt):
                    hits.append(lib)
            if hits: imports.append({"file":rel,"libs":sorted(set(hits))})
            urls=[u for u in URL.findall(txt) if "localhost" not in u and "127.0.0.1" not in u]
            if urls: endpoints.append({"file":rel,"endpoints":sorted(set(urls))[:10]})
    json.dump({"imports":imports,"endpoints":endpoints}, open(args.out,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    if imports or endpoints: print("[WARN] Net guard"); sys.exit(3)
    print("[PASS] Net guard"); sys.exit(0)
if __name__=="__main__": main()
