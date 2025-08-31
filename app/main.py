from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .api import endpoints
from .api.chat_endpoints import router as chat_router
from .core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="RLx — IA compañera de grupos (100% offline, sin tokens)"
)

app.include_router(endpoints.router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
