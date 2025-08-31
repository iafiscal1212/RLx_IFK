from fastapi import APIRouter, HTTPException, status
from typing import List

from app.models.chat import ChatMessageIn, ChatDelivery
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/send")
def send_chat_message(message: ChatMessageIn):
    """
    Sends a message to a group or a list of recipients and generates
    localized deliveries for each one.
    """
    try:
        return chat_service.send_message(message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/delivery/{message_id}", response_model=ChatDelivery)
def get_chat_delivery(message_id: str, recipient: str):
    """
    Retrieves a specific, localized delivery of a message for a given recipient.
    """
    delivery = chat_service.get_delivery(message_id, recipient)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery for message '{message_id}' to recipient '{recipient}' not found."
        )
    return delivery
