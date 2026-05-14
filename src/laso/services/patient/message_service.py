"""Message service — send, list, and manage conversations."""

import logging
from uuid import uuid4

from laso.exceptions import NotFoundError, ValidationError
from laso.models.message import Conversation, Message
from laso.utils.pagination import encode_cursor
from laso.utils.db import execute

log = logging.getLogger(__name__)


def send(patient_id: str, sender_id: str, sender_role: str, sender_name: str, text: str) -> dict:
    log.info("message_service.send | patient_id=%s sender_id=%s", patient_id, sender_id)

    if not patient_id:
        raise ValidationError("patient_id is required")
    if not text:
        raise ValidationError("text is required")

    conversation = Conversation.get_or_create(patient_id, str(uuid4()))

    message = Message(
        message_id=str(uuid4()),
        conversation_id=conversation.conversation_id,
        sender_id=sender_id,
        sender_role=sender_role,
        sender_name=sender_name or sender_role,
        text=text,
    )
    message.save()

    log.info("message_service.send | message_id=%s conversation_id=%s", message.message_id, conversation.conversation_id)
    return message.to_dict()


def get_messages(conversation_id: str, after=None, limit: int = 50) -> dict:
    log.info("message_service.get_messages | conversation_id=%s after=%s limit=%d", conversation_id, after, limit)

    if after:
        rows = execute(
            "SELECT * FROM messages WHERE conversation_id = %s AND created_at > %s ORDER BY created_at ASC LIMIT %s",
            (conversation_id, after, limit),
        )
    else:
        rows = execute(
            "SELECT * FROM messages WHERE conversation_id = %s ORDER BY created_at ASC LIMIT %s",
            (conversation_id, limit),
        )

    items = [Message.from_row(r).to_dict() for r in rows]
    next_cursor = encode_cursor({"after": items[-1]["created_at"]}) if items else None

    log.info("message_service.get_messages | count=%d", len(items))
    return {"items": items, "next_cursor": next_cursor}


def get_conversation_for_patient(patient_id: str) -> dict:
    log.info("message_service.get_conversation_for_patient | patient_id=%s", patient_id)

    conv = Conversation.get_or_create(patient_id, str(uuid4()))
    return conv.to_dict()


def recent_sent(sender_id: str, limit: int = 5) -> list:
    log.info("message_service.recent_sent | sender_id=%s limit=%d", sender_id, limit)

    rows = execute(
        """SELECT m.*, c.patient_id, p.name AS patient_name
           FROM messages m
           JOIN conversations c ON c.conversation_id = m.conversation_id
           JOIN patients p ON p.patient_id = c.patient_id
           WHERE m.sender_id = %s
           ORDER BY m.created_at DESC LIMIT %s""",
        (sender_id, limit),
    )

    results = []
    for r in rows:
        msg = Message.from_row(r).to_dict()
        msg["patient_name"] = r["patient_name"]
        results.append(msg)

    log.info("message_service.recent_sent | count=%d", len(results))
    return results
