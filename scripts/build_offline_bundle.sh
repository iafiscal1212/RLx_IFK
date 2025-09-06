#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
OUTDIR="$ROOT/dist"
APPNAME="rlx"
VERSION_FILE="$ROOT/app/VERSION.txt"
VERSION="${1:-$(date +%Y.%m.%d)}"
[ -f "$VERSION_FILE" ] && VERSION="$(cat "$VERSION_FILE")"

rm -rf "$OUTDIR" && mkdir -p "$OUTDIR"
TARBALL="$OUTDIR/${APPNAME}-${VERSION}-offline.tar.gz"

MANIFEST="$OUTDIR/BUNDLE_MANIFEST.json"
python - <<PY
import json, os, hashlib, pathlib
root = pathlib.Path("$ROOT")
include = [
    "app", "bin", "local_bundle", "scripts", "requirements.txt", "Makefile", "docs/QUICKSTART.md"
]
files = []
for inc in include:
    p = root / inc
    if p.is_file():
        files.append(p)
    else:
        for fp in p.rglob('*'):
            if fp.is_file():
                files.append(fp)
items = []
for f in files:
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    items.append({"path": str(f.relative_to(root)), "sha256": h, "bytes": f.stat().st_size})
(pathlib.Path("$OUTDIR")/"BUNDLE_MANIFEST.json").write_text(json.dumps({"files": items}, indent=2))
PY

tar -czf "$TARBALL" \
  --exclude-vcs \
  -C "$ROOT" app bin local_bundle scripts requirements.txt Makefile docs/QUICKSTART.md

# SHA256SUMS
(
  cd "$OUTDIR"
  sha256sum "$(basename "$TARBALL")" BUNDLE_MANIFEST.json > SHA256SUMS.txt
)

echo "Bundle listo: $TARBALL"
