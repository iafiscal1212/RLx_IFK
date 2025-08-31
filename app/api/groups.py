from fastapi import APIRouter, Body, HTTPException, status, Depends, Query

from ..models import schemas
from ..services import group_service
from ..core.utils import validate_group_id

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)

@router.post("/{group_id}/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_message(group_id: str, message: schemas.MessageIngest):
    """Ingiere y procesa un nuevo mensaje para un grupo."""
    try:
        group_service.persist_message(group_id, message)
        return {"status": "accepted"}
    except Exception as e:
        # En un sistema real, aquí se registraría el error.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{group_id}/state")
def get_group_state(group_id: str):
    """Devuelve el estado completo (memoria YAML) de un grupo."""
    state = group_service.get_group_state(group_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado.")
    return state

@router.get("/{group_id}/affective_state", response_model=schemas.AffectiveStateResponse)
def get_group_affective_state(group_id: str):
    """Devuelve la 'temperatura emocional' actual del grupo."""
    return group_service.get_group_affective_state(group_id)

@router.get("/{group_id}/affective_history", response_model=schemas.AffectiveHistoryResponse)
def get_group_affective_history(
    group_id: str,
    since_hours: int = Query(24, ge=1, le=168, description="Ventana de tiempo en horas para el historial.")
):
    """Devuelve un historial de puntos de 'arousal' para el grupo."""
    try:
        validate_group_id(group_id)
        return group_service.get_affective_history(group_id, since_hours)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
