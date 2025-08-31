from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any

class ChatMessageIn(BaseModel):
    author: str
    text: str
    ts: datetime = Field(default_factory=datetime.utcnow)
    group_id: str | None = None
    recipients: List[str] | None = None

class ChatDelivery(BaseModel):
    message_id: str
    src_lang: str
    target_lang: str
    original_text: str
    gloss_view: Dict[str, Any]
    meta: Dict[str, Any]
    ui_copy: Dict[str, Any]
