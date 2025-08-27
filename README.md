# RLx_IFK — Núcleo local (OFFLINE)

RLx es una **IA compañera de grupos** que opera 100% **sin nube y sin tokens**.  
Modo *observer* por defecto: interviene solo con `@RLX` o por políticas éticas (alerta).

## Principios
- **Sin Token · Sin Nube** (egress=0 en producción).
- **Memoria YAML** por grupo (objetivos, decisiones, hechos).
- **Transparencia**: todo queda trazado en ficheros legibles.
- **Mínimo suficiente**: modelos ligeros + Ley de Hick (2–3 opciones).

## Estructura
app/              # FastAPI (endpoints locales)
local_bundle/     # datos/modelos/grupos (NO se sube al repo)
scripts/          # utilidades (parches, chat local)
ui/               # interfaz mínima

## Arranque rápido

### En tu PC (local)
```bash
cd ~/RLX_IFK
make dev        # te deja todo editable
make run        # arranca RLx en 127.0.0.1:8717
```
Ahora abre: `http://127.0.0.1:8717`

### En GitHub Codespaces (Guía detallada)

#### Paso 1 — Arranque limpio en la terminal
En la terminal de Codespaces (no la de tu PC):
```bash
# 0) Mata cualquier uvicorn viejo
pkill -f "uvicorn.*8717" 2>/dev/null || true

# 1) Asegúrate de estar en la carpeta del repo
# El path debe ser /workspaces/RLx_IFK o similar
cd /workspaces/RLx_IFK

# 2) Activa venv e instala dependencias
source .venv/bin/activate 2>/dev/null || (python3.11 -m venv .venv && source .venv/bin/activate)
pip install -q fastapi uvicorn pyyaml regex psutil

# 3) Arranca escuchando en TODAS las interfaces del contenedor
uvicorn app.main:app --host 0.0.0.0 --port 8717 --reload
```
La terminal debe mostrar `Uvicorn running on http://0.0.0.0:8717`. Déjala abierta.

#### Paso 2 — Abrir el puerto desde la UI de Codespaces
1.  Abajo, en VS Code, ve a la pestaña **Ports**.
2.  Debe aparecer el puerto **8717**. Si no, haz click en **Add Port** y añádelo.
3.  Click derecho en el 8717 → **Open in Browser**.
4.  Se abrirá una URL como `https://8717-<tu-codespace>.githubpreview.dev/`. Esa es la correcta.

> **Nota**: No abras `127.0.0.1:8717` en tu portátil; ese es tu PC, no el contenedor.

#### Paso 3 — Si el puerto sigue sin salir (Troubleshooting)
Abre otra terminal en Codespaces y verifica:
```bash
# ¿Está escuchando el proceso?
ss -ltnp | grep 8717
# Debe mostrar 0.0.0.0:8717 LISTEN

# ¿Está el proceso corriendo?
ps aux | grep uvicorn | grep 8717
```
Si no aparece, Uvicorn no arrancó. Asegúrate de que el fichero `app/main.py` existe y que estás en la carpeta raíz del proyecto (`/workspaces/RLx_IFK`).

## Endpoints
- **System**: `GET /health`
- **Groups**: `GET /groups`, `POST /groups`
- **Group Interaction**:
  - `POST /groups/{id}/ingest`
  - `POST /groups/{id}/respond`
  - `GET /groups/{id}/state`, `GET /groups/{id}/log`, `GET /groups/{id}/export`
  - `GET /groups/{id}/canvas`, `POST /groups/{id}/canvas`
- **Users**: `GET /users`, `POST /users`
- **Projects**: `GET /projects`, `POST /projects`
- **Files**: `GET /files`, `POST /files/upload`, `GET /files/{fid}`
- **Learning**: `POST /feedback`

## Packaging offline
Ver `scripts/build_offline_bundle.sh` (manifiestos de hash + NO-NET).

## Licencias
- Código RLx: EULA on-prem (`licenses/EULA_RLX_ONPREM_v1.0.md`)
- Terceros: `licenses/THIRD_PARTY_NOTICES.md`
