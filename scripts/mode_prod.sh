#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/RLX_IFK"
SRV=rlx
UNIT=/etc/systemd/system/${SRV}.service

echo "[*] Preparando permisos de producción…"
# Código de solo lectura para todos (propietario root)
sudo chown -R root:root "$ROOT/app" "$ROOT/scripts" "$ROOT/ui" "$ROOT/licenses" "$ROOT/README.md" 2>/dev/null || true
sudo chmod -R a-w "$ROOT/app" "$ROOT/scripts" "$ROOT/ui" "$ROOT/licenses" "$ROOT/README.md" 2>/dev/null || true
# Datos de ejecución sólo para rlxsvc
sudo useradd -r -s /usr/sbin/nologin rlxsvc 2>/dev/null || true
sudo chown -R rlxsvc:rlxsvc "$ROOT/local_bundle"
# Quitar ACLs de desarrollo
sudo setfacl -Rb "$ROOT/local_bundle" 2>/dev/null || true

echo "[*] Escribiendo unit systemd con sandbox y sin red (excepto loopback)…"
sudo tee "$UNIT" >/dev/null <<UNIT
[Unit]
Description=RLx (offline, no-net except localhost)
After=network.target
StartLimitIntervalSec=0

[Service]
User=rlxsvc
Group=rlxsvc
WorkingDirectory=$ROOT
Environment=PYTHONUNBUFFERED=1
Environment=RLX_ALLOW_LLM=0
ExecStart=$ROOT/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8717

# Sandbox y no-net
IPAddressDeny=any
IPAddressAllow=localhost
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$ROOT/local_bundle
NoNewPrivileges=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictSUIDSGID=yes
ProcSubset=pid
RemoveIPC=yes
UMask=0077
SystemCallArchitectures=native

Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT

echo "[*] Recargando systemd y arrancando…"
sudo systemctl daemon-reload
sudo systemctl enable --now "$SRV"
systemctl status "$SRV" --no-pager || true

echo "[OK] Modo PROD activado. Servicio en http://127.0.0.1:8717 (sin salida a red)."
