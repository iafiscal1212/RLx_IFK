#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/RLX_IFK"
SRV=rlx

echo "[*] Parando servicio (si está corriendo)…"
sudo systemctl stop "$SRV" 2>/dev/null || true

echo "[*] Devolviendo permisos de edición al usuario (código)…"
sudo chown -R "$USER:$USER" "$ROOT"

echo "[*] Manteniendo local_bundle para el servicio, pero dándote acceso (ACL)…"
sudo apt-get -y install acl >/dev/null 2>&1 || true
sudo chown -R rlxsvc:rlxsvc "$ROOT/local_bundle"
sudo setfacl -R -m u:"$USER":rwx "$ROOT/local_bundle" || true
sudo setfacl -dR -m u:"$USER":rwx "$ROOT/local_bundle" || true

echo "[OK] Modo DEV activado. Edita libremente y arranca con: uvicorn app.main:app --host 127.0.0.1 --port 8717"
