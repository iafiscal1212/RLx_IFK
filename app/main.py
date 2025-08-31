from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from fastapi.staticfiles import StaticFiles


from .core.config import settings
from .api.endpoints import router as core_router

try:
    from .api.chat_endpoints import router as chat_router
except Exception:
    chat_router = None

try:
    from .api.i18n_endpoints import router as i18n_router
except Exception:
    i18n_router = None

app = FastAPI(
    docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json",
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="RLx — IA compañera de grupos (100% offline, sin tokens)"
)

app.include_router(core_router, prefix="/api/v1")
if chat_router:
    app.include_router(chat_router, prefix="/api/v1")
if i18n_router:
    app.include_router(i18n_router, prefix="/api/v1")



# UI-Lite en raíz (ZTL, estática)
app.mount("/", StaticFiles(directory="ui-lite", html=True), name="ui")
