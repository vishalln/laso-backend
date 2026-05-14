"""Base model mixin — defines the interface all domain models follow."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from laso.utils.db import execute_one, insert as db_insert

log = logging.getLogger(__name__)


@dataclass
class BaseModel:
    """Mixin defining the standard model interface: to_dict, save, from_row."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = field(default=None, repr=False)
    updated_at: Optional[datetime] = field(default=None, repr=False)

    def to_dict(self) -> Dict:
        """Serialize to API-safe dict. Override for custom serialization."""
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                result[k] = None
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif hasattr(v, "value"):
                result[k] = v.value
            else:
                result[k] = v
        return result

    def save(self) -> None:
        """Persist to PostgreSQL. Subclasses must define _insert_sql and to_params."""
        sql = getattr(self, "_insert_sql", None)
        if not sql:
            raise NotImplementedError("Subclass must define _insert_sql")
        log.info("%s.save | id=%s", self.__class__.__name__, self.id)
        db_insert(sql, self.to_params())
        log.info("%s.save | success | id=%s", self.__class__.__name__, self.id)

    def to_params(self) -> tuple:
        """Serialize to SQL parameter tuple. Override in subclass."""
        raise NotImplementedError

    @classmethod
    def from_row(cls, row: Dict) -> "BaseModel":
        """Construct from a database row dict. Override in subclass."""
        raise NotImplementedError
