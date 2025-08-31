#!/usr/bin/env python3
import sys, os, re, json, argparse, pathlib
EXTS={".py",".rs",".js",".ts",".tsx",".jsx",".json",".yaml",".yml",".toml",".env",".ini",".cfg",".md",".sh",".ps1"}
API=[r"OPENAI_API_KEY", r"ANTHROPIC_API_KEY", r"HUGGINGFACE", r"COHERE_API_KEY", r"GROQ_API_KEY", r"MISTRAL_API_KEY", r"\bAPI_KEY\b", r"SECRET_KEY", r"BEARER\s+[A-Za-z0-9\-\.~\+\/]+"]
CMD=[r"\bcurl\s", r"\bwget\s", r"\biwr\s", r"\binvoke-webrequest\b", r"\bnc\s", r"\bncat\s"]
def read(p):
    try: return open(p,"r",encoding="utf-8",errors="ignore").read()
    except: return ""
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--out",default="reports/secrets_guard_report.json"); args=ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    api=[]; cmd=[]
    for dp,_,fn in os.walk(args.root):
        for f in fn:
            if pathlib.Path(f).suffix.lower() not in EXTS: continue
            p=os.path.join(dp,f); txt=read(p); rel=os.path.relpath(p,args.root)
            for pat in API:
                if re.search(pat, txt): api.append({"file":rel,"pattern":pat}); break
            for pat in CMD:
                if re.search(pat, txt, flags=re.IGNORECASE): cmd.append({"file":rel,"pattern":pat}); break
    json.dump({"api_markers":api,"cmd_suspects":cmd}, open(args.out,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    if api or cmd: print("[WARN] Secrets guard"); sys.exit(4)
    print("[PASS] Secrets guard"); sys.exit(0)
if __name__=="__main__": main()
