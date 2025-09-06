#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
export PYTHONPATH="$ROOT"
"$ROOT/bin/rlxd" &
PID=$!
sleep 1
# Ingesta de un mensaje para ver el z subir
curl -sS -X POST "http://127.0.0.1:8717/api/v1/groups/equipo-demo/ingest" \
  -H 'content-type: application/json' \
  -d '{"author":"carmen","text":"ESTO ES URGENTE!!!!"}' | jq . || true
# Consulta de respuesta
curl -sS -X POST "http://127.0.0.1:8717/api/v1/groups/equipo-demo/respond" | jq . || true
kill "$PID" || true