from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api import groups, files
from .models import schemas

# --- Creación de la aplicación principal ---
app = FastAPI(
    title="RLx IFK Core",
    description="Núcleo local y sin conexión para la IA compañera de grupos RLx.",
    version="1.0.0"
)

# --- Router para la API v1 ---
# Agrupamos todos los endpoints de la API bajo /api/v1
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(groups.router)
api_router.include_router(files.router)

@api_router.get("/health", response_model=schemas.Health, tags=["health"])
def health_check():
    """Comprueba que el servicio está en línea."""
    return {"status": "ok", "message": "RLx service is running."}

app.include_router(api_router)

# --- Servir la Interfaz de Usuario (Frontend) ---
# Esto es crucial: monta el directorio 'ui-lite' en la raíz.
# `html=True` permite que `index.html` se sirva para rutas como '/'.
ui_path = Path(__file__).parent.parent / "ui-lite"
app.mount("/", StaticFiles(directory=ui_path, html=True), name="ui")
