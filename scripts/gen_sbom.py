#!/usr/bin/env python3
import os, re, json, argparse, pathlib, hashlib, datetime
MODEL={".onnx",".pt",".bin",".gguf",".safetensors",".pb",".tflite",".mlmodel"}
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): h.update(c)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--out",default="sbom.json"); a=ap.parse_args()
    files=[os.path.join(dp,f) for dp,_,fn in os.walk(a.root) for f in fn]
    proj={os.path.relpath(p,a.root):p for p in files}
    sb={"generated_at":datetime.datetime.utcnow().isoformat()+"Z","files":len(files),"manifests":{},"models":[]}
    if "requirements.txt" in proj:
        lines=open(proj["requirements.txt"],"r",encoding="utf-8",errors="ignore").read().splitlines()
        req=[re.split(r"[#;]",l)[0].strip() for l in lines if l.strip() and not l.strip().startswith("#")]
        sb["manifests"]["requirements.txt"]=req
    if "package.json" in proj:
        try:
            pkg=json.loads(open(proj["package.json"],"r",encoding="utf-8").read() or "{}")
            sb["manifests"]["package.json"]={"name":pkg.get("name"),"dependencies":pkg.get("dependencies",{}),"devDependencies":pkg.get("devDependencies",{})}
        except: sb["manifests"]["package.json"]={"error":"parse_error"}
    for rel,full in proj.items():
        if pathlib.Path(rel).suffix.lower() in MODEL:
            sb["models"].append({"file":rel,"sha256":sha(full),"size":os.path.getsize(full)})
    json.dump(sb, open(a.out,"w",encoding="utf-8"), indent=2, ensure_ascii=False); print("[OK]", a.out)
if __name__=="__main__": main()