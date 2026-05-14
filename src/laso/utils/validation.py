"""Request validation utilities."""

import logging
import uuid as uuid_mod
from enum import Enum
from typing import Any

from laso.exceptions import ValidationError

log = logging.getLogger(__name__)


def validate_required(body: dict, fields: list[str]) -> None:
    """Raise ValidationError if any field is missing or None."""
    missing = [f for f in fields if not body.get(f)]
    if missing:
        log.warning("validate_required | missing=%s", missing)
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing)}",
            details={"missing_fields": missing},
        )


def validate_enum(value: Any, enum_class: type[Enum], field_name: str) -> None:
    """Raise ValidationError if value is not a valid enum member."""
    valid = [e.value for e in enum_class]
    if value not in valid:
        log.warning("validate_enum | field=%s value=%s", field_name, value)
        raise ValidationError(
            message=f"Invalid value for {field_name}: '{value}'",
            details={"field": field_name, "valid_values": valid},
        )


def validate_max_length(value: str, max_len: int, field_name: str) -> None:
    """Raise ValidationError if string exceeds max length."""
    if value and len(value) > max_len:
        log.warning("validate_max_length | field=%s len=%d max=%d", field_name, len(value), max_len)
        raise ValidationError(
            message=f"{field_name} exceeds maximum length of {max_len}",
            details={"field": field_name, "max_length": max_len},
        )


def validate_transition(current, target, enum_class: type[Enum]) -> None:
    """Raise ValidationError if transition is not allowed by enum's valid_transitions."""
    transitions = enum_class.valid_transitions()
    allowed = transitions.get(current, [])
    if target not in allowed:
        log.warning("validate_transition | current=%s target=%s allowed=%s", current, target, allowed)
        raise ValidationError(
            message=f"Invalid transition from '{current.value}' to '{target.value}'",
            details={"current": current.value, "target": target.value, "allowed": [a.value for a in allowed]},
        )


def validate_uuid(value: str, field_name: str) -> None:
    """Raise ValidationError if value is not a valid UUID."""
    try:
        uuid_mod.UUID(value)
    except (ValueError, AttributeError):
        log.warning("validate_uuid | field=%s value=%s", field_name, value)
        raise ValidationError(
            message=f"Invalid UUID for {field_name}: '{value}'",
            details={"field": field_name},
        )
