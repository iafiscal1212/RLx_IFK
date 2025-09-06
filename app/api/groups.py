from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.core.utils import validate_group_id
from app.services.group_service import (
    ensure_group,
    append_message,
    get_group_state,
)
from app.core.policies import get_threshold_z

router = APIRouter(prefix="/groups", tags=["groups"])


class IngestIn(BaseModel):
    author: str = Field(..., min_length=1, max_length=40)
    text: str = Field(..., min_length=1, max_length=4000)
    timestamp: Optional[str] = None  # ISO8601 opcional


@router.post("/{group_id}/ingest")
async def ingest(group_id: str, body: IngestIn) -> Dict[str, Any]:
    gid = validate_group_id(group_id)
    ensure_group(gid)
    s = append_message(gid, author=body.author, text=body.text, timestamp=body.timestamp)
    return {
        "ok": True,
        "group_id": gid,
        "arousal_z": s["metrics"].get("arousal_z", 0.0),
        "n_messages": s["metrics"].get("n_messages", 0),
    }


class RespondOut(BaseModel):
    alert: Optional[str] = None
    arousal_z: float
    threshold_z: float
    suggestions: List[str] = []


@router.post("/{group_id}/respond", response_model=RespondOut)
async def respond(group_id: str) -> RespondOut:
    gid = validate_group_id(group_id)
    st = get_group_state(gid)
    if st is None:
        raise HTTPException(status_code=404, detail="group not found")
    z = float(st["metrics"].get("arousal_z", 0.0))
    th = float(get_threshold_z())
    if z >= th:
        return RespondOut(
            alert="arousal_spike_detected",
            arousal_z=z,
            threshold_z=th,
            suggestions=[
                "Pausa de 90 s: respirad y retomad con idea principal en 1 frase.",
                "Reencuadre: cada uno aporta un hecho verificable y una petición concreta.",
            ],
        )
    return RespondOut(alert=None, arousal_z=z, threshold_z=th, suggestions=[])


@router.get("/{group_id}/state")
async def state(group_id: str) -> Dict[str, Any]:
    gid = validate_group_id(group_id)
    st = get_group_state(gid)
    if st is None:
        raise HTTPException(status_code=404, detail="group not found")
    return st
