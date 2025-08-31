#!/usr/bin/env python3
import os, re, json, argparse, pathlib, hashlib, datetime
MODEL={".onnx",".pt",".bin",".gguf",".safetensors",".pb",".tflite",".mlmodel"}
def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="sbom.json")
    args = ap.parse_args()

    files = [os.path.join(dp, f) for dp, _, fn in os.walk(args.root) for f in fn]
    proj = {os.path.relpath(p, args.root): p for p in files}
    sbom = {"generated_at": datetime.datetime.utcnow().isoformat() + "Z", "files": len(files), "manifests": {}, "models": []}

    if "requirements.txt" in proj:
        with open(proj["requirements.txt"], "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
        req = [re.split(r"[#;]", l)[0].strip() for l in lines if l.strip() and not l.strip().startswith("#")]
        sbom["manifests"]["requirements.txt"] = req

    if "package.json" in proj:
        try:
            with open(proj["package.json"], "r", encoding="utf-8") as f:
                pkg = json.loads(f.read() or "{}")
            sbom["manifests"]["package.json"] = {"name": pkg.get("name"), "dependencies": pkg.get("dependencies", {}), "devDependencies": pkg.get("devDependencies", {})}
        except (json.JSONDecodeError, FileNotFoundError):
            sbom["manifests"]["package.json"] = {"error": "parse_error"}

    for rel, full in proj.items():
        if pathlib.Path(rel).suffix.lower() in MODEL:
            sbom["models"].append({"file": rel, "sha256": get_sha256(full), "size": os.path.getsize(full)})

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2, ensure_ascii=False)
    print(f"[OK] SBOM generated: {args.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
