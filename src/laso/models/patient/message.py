"""Messaging domain models — Conversation and Message."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Conversation:
    conversation_id: str
    patient_id: str
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "conversation_id": self.conversation_id,
            "patient_id": self.patient_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Conversation":
        return cls(
            conversation_id=row["conversation_id"],
            patient_id=row["patient_id"],
            created_at=row.get("created_at"),
        )

    def save(self) -> None:
        log.info("Conversation.save | conversation_id=%s", self.conversation_id)
        insert(
            "INSERT INTO conversations (conversation_id, patient_id) VALUES (%s,%s)",
            (self.conversation_id, self.patient_id),
        )

    @classmethod
    def get_for_patient(cls, patient_id: str) -> Optional["Conversation"]:
        row = execute_one(
            "SELECT * FROM conversations WHERE patient_id = %s LIMIT 1",
            (patient_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def get_or_create(cls, patient_id: str, conversation_id: str) -> "Conversation":
        existing = cls.get_for_patient(patient_id)
        if existing:
            return existing
        conv = cls(conversation_id=conversation_id, patient_id=patient_id)
        conv.save()
        return conv


@dataclass
class Message:
    message_id: str
    conversation_id: str
    sender_id: str
    sender_role: str
    sender_name: str
    text: str
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role,
            "sender_name": self.sender_name,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Message":
        return cls(
            message_id=row["message_id"],
            conversation_id=row["conversation_id"],
            sender_id=row["sender_id"],
            sender_role=row["sender_role"],
            sender_name=row["sender_name"],
            text=row["text"],
            created_at=row.get("created_at"),
        )

    def save(self) -> None:
        log.info("Message.save | message_id=%s", self.message_id)
        insert(
            """INSERT INTO messages (message_id, conversation_id, sender_id,
               sender_role, sender_name, text)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (self.message_id, self.conversation_id, self.sender_id,
             self.sender_role, self.sender_name, self.text),
        )

    @classmethod
    def list_for_conversation(
        cls, conversation_id: str, after: Optional[datetime] = None, limit: int = 50
    ) -> List["Message"]:
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
        return [cls.from_row(r) for r in rows]
