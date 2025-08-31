from fastapi import APIRouter, Body, HTTPException, status, Depends, Query
from pathlib import Path
from datetime import datetime
import re

from ..models import schemas
from ..services import group_service
from ..core.utils import validate_group_id

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)

@router.get("/", response_model=schemas.GroupListResponse)
def list_groups():
    """
    Lista todos los grupos (proyectos) disponibles, ordenados por modificación reciente.
    """
    groups_dir = Path("local_bundle/groups")
    if not groups_dir.exists():
        return {"groups": []}

    group_files = sorted(
        groups_dir.glob("*.yaml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    groups_info = [
        schemas.GroupInfo(
            group_id=p.stem,
            last_modified=datetime.fromtimestamp(p.stat().st_mtime),
            has_recent_alerts=group_service.has_recent_alerts(p.stem)
        ) for p in group_files
    ]
    return {"groups": groups_info}

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.GroupInfo)
def create_new_group(group_data: schemas.CreateGroupRequest):
    """
    Crea un nuevo grupo (proyecto).
    """
    group_id = group_data.group_id
    template = group_data.template
    # Validación estricta del nombre en la capa de API
    if not re.match(r"^[a-zA-Z0-9_-]+$", group_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del proyecto solo puede contener letras, números, guiones y guiones bajos."
        )

    try:
        filepath = group_service.create_group(group_id, template=template)
        return schemas.GroupInfo(
            group_id=group_id,
            last_modified=datetime.fromtimestamp(filepath.stat().st_mtime)
        )
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e: # Captura la validación de get_group_memory_path
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{group_id}", status_code=status.HTTP_200_OK, response_model=schemas.GroupInfo)
def rename_group(group_id: str, rename_data: schemas.RenameGroupRequest):
    """
    Renombra un grupo (proyecto).
    """
    new_group_id = rename_data.new_group_id
    if not re.match(r"^[a-zA-Z0-9_-]+$", new_group_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nuevo ID del proyecto solo puede contener letras, números, guiones y guiones bajos."
        )

    try:
        group_service.rename_group(group_id, new_group_id)
        new_filepath = group_service.get_group_memory_path(new_group_id)
        return schemas.GroupInfo(group_id=new_group_id, last_modified=datetime.fromtimestamp(new_filepath.stat().st_mtime))
    except (FileNotFoundError, FileExistsError, ValueError, IOError) as e:
        # Asignar códigos de estado HTTP apropiados
        status_code = 404 if isinstance(e, FileNotFoundError) else 409 if isinstance(e, FileExistsError) else 400
        raise HTTPException(status_code=status_code, detail=str(e))

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: str):
    """
    Elimina un grupo (proyecto) de forma permanente.
    """
    try:
        group_service.delete_group(group_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except ValueError as e: # Captura la validación de get_group_memory_path
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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

@router.get("/{group_id}/metrics", response_model=schemas.GroupMetricsResponse)
def get_group_metrics(group_id: str):
    """Devuelve las métricas clave del grupo en tiempo real."""
    try:
        validate_group_id(group_id)
        return group_service.get_group_metrics(group_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        # Log the error in a real app
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al calcular las métricas del grupo.")

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
