#!/usr/bin/env bash
set -euo pipefail
echo "=== RLx STATUS ==="
echo "[service]"; systemctl is-active rlx || true
echo "[unit]"; systemctl show -p FragmentPath -p MainPID rlx 2>/dev/null || true
echo "[port]"; ss -ltnp | grep 8717 || echo "no listening on :8717"
echo "[files]"; ls -ld $HOME/RLX_IFK $HOME/RLX_IFK/local_bundle 2>/dev/null || true
echo "[net sandbox]"
systemctl cat rlx | sed -n 's/^\s*\(IPAddress.*\|Protect.*\|Restrict.*\|NoNewPrivileges.*\|ReadWritePaths.*\)/\1/p'
echo "==============="
