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

## Ejecutar en local
python3.11 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pyyaml regex psutil
uvicorn app.main:app --host 127.0.0.1 --port 8717

## Endpoints
- GET /health
- POST /groups/{id}/ingest   (body: {author,text,ts?})
- POST /groups/{id}/respond  (responde si hay trigger)
- GET /groups/{id}/state

## Packaging offline
Ver `scripts/build_offline_bundle.sh` (manifiestos de hash + NO-NET).

## Licencias
- Código RLx: EULA on-prem (`licenses/EULA_RLX_ONPREM_v1.0.md`)
- Terceros: `licenses/THIRD_PARTY_NOTICES.md`
