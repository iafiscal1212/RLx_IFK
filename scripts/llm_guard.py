#!/usr/bin/env python3
import sys, os, re, json, argparse, pathlib
from .utils import read_file_content

BANNED = ["openai","anthropic","transformers","sentence_transformers","vllm","llama_cpp","llama-cpp-python","llama","gptq","exllama","auto_gptq","ctransformers","rwkv","ollama","langchain","llama_index","gpt4all","mistralai","groq","cohere","replicate","huggingface_hub","accelerate"]
CRATES = ["llama","llm","gpt","tokenizers"]
EXTS = {".py",".js",".ts",".tsx",".jsx",".json",".yaml",".yml",".toml",".md"}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--out",default="reports/llm_guard_report.json"); args=ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    viol=[]
    for dp,_,fn in os.walk(args.root):
        for f in fn:
            if pathlib.Path(f).suffix.lower() not in EXTS: continue
            txt=read_file_content(os.path.join(dp,f)).lower(); rel=os.path.relpath(os.path.join(dp,f), args.root)
            hits=[b for b in BANNED if re.search(rf'(?m)^\s*(from\s+{re.escape(b)}\s+import|import\s+{re.escape(b)}\b)|require\(["\']{re.escape(b)}["\']\)', txt)]
            if hits: viol.append({"file":rel,"items":sorted(set(hits))})
            if f=="Cargo.toml":
                hits=[c for c in CRATES if re.search(rf'\b{re.escape(c)}\b', txt)]
                if hits: viol.append({"file":rel,"items":sorted(set(hits))})
    json.dump({"violations":viol}, open(args.out,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    if viol: print("[FAIL] LLM guard"); sys.exit(2)
    print("[PASS] LLM guard"); sys.exit(0)
if __name__=="__main__": main()
