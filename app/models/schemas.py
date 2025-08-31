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

class AlertDetails(BaseModel):
    value: float
    threshold: float
    rationale: str

class AlertRecord(BaseModel):
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "RLx"
    type: str = "alert"
    alert_type: str = "arousal_spike_detected"
    trigger_ref: str = Field(description="ID del mensaje que disparó la alerta.")
    details: AlertDetails

class AffectiveStateResponse(BaseModel):
    group_arousal_z: float = Field(description="Mediana normalizada del Arousal del grupo en la última ventana de tiempo.")
    active_users: int = Field(description="Número de usuarios que contribuyeron al cálculo.")

class AffectiveHistoryPoint(BaseModel):
    ts: datetime = Field(description="Timestamp del punto de datos.")
    value: float = Field(description="Valor de arousal_z en ese momento.")

class AffectiveHistoryResponse(BaseModel):
    history: list[AffectiveHistoryPoint]

class SuggestionDetails(BaseModel):
    rationale: str
    suggestion_text: str

class SuggestionRecord(BaseModel):
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "RLx"
    type: str = "suggestion"
    suggestion_type: str = "proactive_pause"
    details: SuggestionDetails

# --- Modelos para el Resumen Diario ---

class ActionItem(BaseModel):
    assignee: str = Field(description="Persona a la que se le asignó la acción.")
    task: str = Field(description="Descripción de la tarea o acción.")

class DailySummaryDetails(BaseModel):
    topics: list[str] = Field(description="Temas más discutidos extraídos del día.")
    decisions: list[str] = Field(description="Decisiones o acuerdos clave identificados.")
    actions: list[ActionItem] = Field(description="Acciones o tareas asignadas a miembros del equipo.")
    general_sentiment: float | None = Field(None, description="Sentimiento general del día (-1 a 1, basado en la media de valence_z).")
    message_count: int = Field(description="Número de mensajes analizados para este resumen.")

class DailySummaryRecord(BaseModel):
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "RLx"
    type: str = "daily_summary"
    details: DailySummaryDetails

# --- Modelos para la lista de grupos ---

class GroupInfo(BaseModel):
    group_id: str
    last_modified: datetime

class GroupListResponse(BaseModel):
    groups: list[GroupInfo]

# --- Modelo para crear un grupo ---

class CreateGroupRequest(BaseModel):
    group_id: str = Field(..., description="El ID del nuevo grupo a crear. Debe ser alfanumérico con guiones/guiones bajos.")

# --- Modelo para renombrar un grupo ---

class RenameGroupRequest(BaseModel):
    new_group_id: str = Field(..., description="El nuevo ID para el proyecto.")
