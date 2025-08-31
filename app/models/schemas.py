from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Health(BaseModel):
    status: str
    message: str

class MessageIngest(BaseModel):
    author: str = Field(..., description="Autor del mensaje.")
    text: str = Field(..., description="Contenido del mensaje.")
    ts: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del mensaje (UTC).")

class AffectiveProxy(BaseModel):
    raw_arousal: float
    raw_valence: float
    raw_uncertainty: float
    arousal_z: float = Field(description="Puntuación Z normalizada de Arousal.")
    valence_z: float = Field(description="Puntuación Z normalizada de Valence.")
    uncertainty_z: float = Field(description="Puntuación Z normalizada de Uncertainty.")
    e_user: float = Field(description="Carga emocional del usuario (0 a 1).")

class MessageRecord(MessageIngest):
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único del mensaje.")
    type: str = "message"
    actor: str # This will be the same as author
    affective_proxy: AffectiveProxy | None = None
