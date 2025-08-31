import yaml
import json
from pathlib import Path
from datetime import datetime

from app.models.chat import ChatMessageIn, ChatDelivery
from i18n.detect import detect_lang
from renderer import interlingua, localize

PROFILES_DIR = Path("profiles")
CHAT_DIR = Path("local_bundle/chat")


def _load_profiles():
    """Loads user and group profiles from YAML files."""
    with open(PROFILES_DIR / "users.yaml", "r") as f:
        users = yaml.safe_load(f)
    with open(PROFILES_DIR / "groups.yaml", "r") as f:
        groups = yaml.safe_load(f)
    return users, groups


def send_message(message: ChatMessageIn):
    """
    Persists a message and creates deliveries for each recipient.
    """
    users, groups = _load_profiles()
    message_id = f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S%f')}"
    src_lang = detect_lang(message.text)

    # Persist original message
    msg_path = CHAT_DIR / "messages"
    msg_path.mkdir(parents=True, exist_ok=True)
    with open(msg_path / f"{message_id}.json", "w") as f:
        json.dump(message.model_dump(mode='json'), f, indent=2)

    # Determine recipients
    if message.group_id and message.group_id in groups:
        recipients = groups[message.group_id].get("users", [])
    elif message.recipients:
        recipients = message.recipients
    else:
        raise ValueError("No recipients or valid group_id provided.")

    # Create deliveries
    deliveries = []
    for recipient in recipients:
        if recipient == message.author:
            continue # Don't deliver to self

        target_lang = users.get(recipient, {}).get("lang") or \
                      groups.get(message.group_id, {}).get("default_lang") or \
                      "es"

        # Build neutral structure
        structure = interlingua.build_structure(message.text)
        structure['src_lang'] = src_lang

        # Localize
        gloss_view = localize.localize(structure, target_lang)

        delivery = ChatDelivery(
            message_id=message_id,
            src_lang=src_lang,
            target_lang=target_lang,
            original_text=message.text,
            gloss_view=gloss_view,
            meta={"author": message.author, "group_id": message.group_id, "recipients": [recipient]},
            ui_copy={"badges": [f"{src_lang.upper()}→{target_lang.upper()}"]}
        )

        # Persist delivery
        delivery_path = CHAT_DIR / "deliveries" / message_id
        delivery_path.mkdir(parents=True, exist_ok=True)
        delivery_ref = delivery_path / f"{recipient}.json"
        with open(delivery_ref, "w") as f:
            json.dump(delivery.model_dump(mode='json'), f, indent=2)

        deliveries.append({"recipient": recipient, "target_lang": target_lang, "delivery_ref": str(delivery_ref)})

    return {"message_id": message_id, "deliveries": deliveries}


def get_delivery(message_id: str, recipient: str):
    """Retrieves a specific delivery for a user."""
    delivery_path = CHAT_DIR / "deliveries" / message_id / f"{recipient}.json"
    if not delivery_path.exists():
        return None
    with open(delivery_path, "r") as f:
        return json.load(f)
