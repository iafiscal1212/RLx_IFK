from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .core.config import settings
from .api.endpoints import router as core_router

# Importa opcionales con try/except para no romper si aún no existen
try:
    from .api.chat_endpoints import router as chat_router  # opcional
except Exception:
    chat_router = None

try:
    from .api.i18n_endpoints import router as i18n_router  # opcional
except Exception:
    i18n_router = None

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="RLx — IA compañera de grupos (100% offline, sin tokens)"
)

# Routers
app.include_router(core_router, prefix="/api/v1")
if chat_router:
    app.include_router(chat_router, prefix="/api/v1")
if i18n_router:
    app.include_router(i18n_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
