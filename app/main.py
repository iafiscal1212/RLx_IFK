from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pathlib import Path

# Activa guard de No-Net en runtime (prohíbe conexiones salientes)
try:
    import scripts.no_net_runtime  # noqa: F401
except Exception:  # dura lex
    pass

from app.api.groups import router as groups_router  # noqa: E402

app = FastAPI(title="RLx API", version="1.0.0", docs_url="/docs", openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


# API
app.include_router(groups_router, prefix="/api/v1")

# Serve UI-Lite si existe
from fastapi.staticfiles import StaticFiles  # noqa: E402

ui_dir = Path(__file__).resolve().parents[1] / "ui-lite"
if ui_dir.exists():
    app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
