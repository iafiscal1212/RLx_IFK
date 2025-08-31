from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from fastapi.staticfiles import StaticFiles


from .api.endpoints import router as system_router
from .api.groups import router as groups_router

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
    title="RLx API",
    version="2.1.0",
    description="RLx — IA compañera de grupos (100% offline, sin tokens)"
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/index.html")

app.include_router(system_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")
if chat_router:
    app.include_router(chat_router, prefix="/api/v1")
if i18n_router:
    app.include_router(i18n_router, prefix="/api/v1")

# UI-Lite en raíz (ZTL, estática)
app.mount("/", StaticFiles(directory="ui-lite", html=True), name="ui")
