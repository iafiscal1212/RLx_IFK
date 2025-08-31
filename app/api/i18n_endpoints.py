import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from app.models.chat import ChatDelivery
from renderer import interlingua, localize
from i18n.detect import detect_lang

router = APIRouter(prefix="/render", tags=["i18n"])

CHAT_MESSAGES_DIR = Path("local_bundle/chat/messages")

@router.get("/summary", response_model=ChatDelivery)
def render_summary(message_id: str, recipient: str, lang: str):
    """
    Renders a localized view of a message on-the-fly for a given
    recipient and target language, without persisting a new delivery.
    """
    message_path = CHAT_MESSAGES_DIR / f"{message_id}.json"
    if not message_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original message not found.")

    with open(message_path, "r", encoding="utf-8") as f:
        original_message = json.load(f)

    original_text = original_message.get("text", "")
    src_lang = detect_lang(original_text)
    target_lang = lang

    # Build neutral structure and add source language for glossary lookup
    structure = interlingua.build_structure(original_text)
    structure['src_lang'] = src_lang

    # Localize using the renderer
    gloss_view = localize.localize(structure, target_lang)

    return ChatDelivery(
        message_id=message_id,
        src_lang=src_lang,
        target_lang=target_lang,
        original_text=original_text,
        gloss_view=gloss_view,
        meta={"author": original_message.get("author"), "group_id": original_message.get("group_id"), "recipients": [recipient]},
        ui_copy={"badges": [f"{src_lang.upper()}→{target_lang.upper()}"]}
    )
