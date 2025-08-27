#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.."; pwd)"
out="$root/local_bundle/dist/rlx_offline_$(date +%Y%m%d%H%M%S).tar.gz"
mkdir -p "$root/local_bundle/dist"

# Manifiesto simple (sha256) si existen data/models locales
python3 - <<'PY'
import os, json, hashlib, pathlib
base="local_bundle"; items=[]
for top in ("data","models","licenses","dist"):
    d=os.path.join(base,top)
    if os.path.isdir(d):
        for dp,_,fs in os.walk(d):
            for f in fs:
                p=os.path.join(dp,f)
                h=hashlib.sha256()
                with open(p,'rb') as fh:
                    for b in iter(lambda:fh.read(1<<20), b''): h.update(b)
                items.append({"path":p, "sha256":h.hexdigest(), "bytes":os.path.getsize(p)})
path="local_bundle/dist/BUNDLE_MANIFEST.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
open(path,"w").write(json.dumps(items, indent=2))
print(f"Wrote {path} with {len(items)} entries")
PY

# Tar reproducible
tar --sort=name --owner=0 --group=0 --mtime='UTC 2024-01-01' -czf "$out" \
  app scripts licenses README.md
echo "Bundle: $out"
