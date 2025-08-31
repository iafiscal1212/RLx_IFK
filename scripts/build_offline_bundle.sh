#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.."; pwd)"
out="$root/local_bundle/dist/rlx_offline_$(date +%Y%m%d%H%M%S).tar.gz"
mkdir -p "$root/local_bundle/dist"

# Generar manifiesto de assets locales usando el script dedicado
echo "[*] Generando manifiesto de assets..."
python3 "$root/scripts/generate_manifest.py"

# Tar reproducible
tar --sort=name --owner=0 --group=0 --mtime='UTC 2024-01-01' -czf "$out" \
  app scripts licenses README.md
echo "Bundle: $out"
