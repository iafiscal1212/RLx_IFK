from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from ..models import schemas
from ..services import group_service

router = APIRouter()

@router.get("/health", tags=["status"])
def health_check():
    """
    Verifica que el servicio esté operativo.
    """
    return {"status": "ok", "message": "RLx service is running"}

@router.post("/groups/{group_id}/ingest", status_code=status.HTTP_202_ACCEPTED, tags=["groups"])
def ingest_message(group_id: str, message: schemas.MessageIngest):
    """
    Ingesta un nuevo mensaje en la memoria de un grupo, calculando
    su Affective Proxy y aplicando políticas éticas.
    """
    try:
        group_service.persist_message(group_id, message)
        return {"status": "accepted", "group_id": group_id}
    except (IOError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al procesar la petición: {e}")

@router.get("/groups/{group_id}/state", response_model=Dict[str, Any], tags=["groups"])
def get_group_state(group_id: str):
    """
    Obtiene el estado completo (memoria YAML) de un grupo.
    """
    state = group_service.get_group_state(group_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Grupo '{group_id}' no encontrado.")
    return state

@router.post("/groups/{group_id}/respond", status_code=status.HTTP_501_NOT_IMPLEMENTED, tags=["groups"])
def trigger_response(group_id: str):
    """
    (No implementado) Invoca a RLx para que analice el estado actual y, si es necesario,
    genere un resumen, opciones o una alerta.
    """
    return {"status": "pending_implementation", "group_id": group_id}
