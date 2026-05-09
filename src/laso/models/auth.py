"""Auth domain models — User, RoleChangeAudit with OO persistence."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict

from laso.constants.sql import AuditSQL
from laso.enums import UserRole
from laso.constants.auth import COGNITO_ATTR, DEFAULT_USER_ROLE
from laso.utils.db import insert

log = logging.getLogger(__name__)


@dataclass
class User:
    id: str
    email: str
    role: UserRole
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_cognito(cls, cognito_data: Dict, groups: List[str]) -> "User":
        attributes = {attr["Name"]: attr["Value"] for attr in cognito_data.get("UserAttributes", [])}
        role = UserRole.from_group_name(groups[0]) if groups else DEFAULT_USER_ROLE
        return cls(
            id=attributes.get(COGNITO_ATTR.SUB, ""),
            email=attributes.get(COGNITO_ATTR.EMAIL, ""),
            role=role,
            name=attributes.get(COGNITO_ATTR.NAME),
        )


@dataclass
class RoleChangeAudit:
    audit_id: str
    target_user_email: str
    previous_role: str
    new_role: str
    changed_by_admin_email: str
    changed_by_admin_id: str

    def to_params(self) -> tuple:
        """Serialize to SQL parameter tuple matching AuditSQL.INSERT column order."""
        return (
            self.audit_id, self.target_user_email,
            self.previous_role, self.new_role,
            self.changed_by_admin_email, self.changed_by_admin_id,
        )

    def save(self) -> None:
        """Persist to PostgreSQL."""
        log.info("RoleChangeAudit.save | audit_id=%s target=%s",
                 self.audit_id, self.target_user_email)
        insert(AuditSQL.INSERT, self.to_params())
        log.info("RoleChangeAudit.save | success | audit_id=%s", self.audit_id)
