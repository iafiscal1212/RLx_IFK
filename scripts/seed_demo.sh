#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
mkdir -p "$ROOT/local_bundle/groups/equipo-demo"
cat > "$ROOT/local_bundle/groups/equipo-demo/messages.yaml" <<'YAML'
- timestamp: "2025-09-06T12:00:00Z"
  author: carmen
  text: "Arrancamos la prueba del grupo equipo-demo."
- timestamp: "2025-09-06T12:00:20Z"
  author: carmen
  text: "¡Esto va bien!"
- timestamp: "2025-09-06T12:00:50Z"
  author: carmen
  text: "NECESITO QUE ESTO SALGA HOY!!"
YAML
echo "Seed listo."