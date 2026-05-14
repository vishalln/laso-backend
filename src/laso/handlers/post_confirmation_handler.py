"""Cognito Post-Confirmation trigger — provisions user record in RDS."""

import logging

from laso.enums import UserRole
from laso.utils.db import insert

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_SQL_PROVISION_PATIENT = """
    INSERT INTO patients (patient_id, email, name, status)
    VALUES (%s, %s, %s, 'active')
    ON CONFLICT (patient_id) DO NOTHING
"""

_SQL_PROVISION_DOCTOR = """
    INSERT INTO doctors (doctor_id, email, name, status)
    VALUES (%s, %s, %s, 'active')
    ON CONFLICT (doctor_id) DO NOTHING
"""


def lambda_handler(event, context):
    log.info("post_confirmation | trigger_source=%s", event.get("triggerSource"))

    attributes = event["request"]["userAttributes"]
    user_sub = attributes["sub"]
    email = attributes.get("email", "")
    name = attributes.get("name", email.split("@")[0])

    groups = event["request"].get("groupConfiguration", {}).get("groupsToOverride", [])
    role = _resolve_role(groups)

    log.info("post_confirmation | sub=%s email=%s role=%s", user_sub, email, role.value)

    if role == UserRole.PATIENT:
        insert(_SQL_PROVISION_PATIENT, (user_sub, email, name))
    elif role == UserRole.DOCTOR:
        insert(_SQL_PROVISION_DOCTOR, (user_sub, email, name))

    log.info("post_confirmation | provisioned | sub=%s role=%s", user_sub, role.value)
    return event


def _resolve_role(groups: list[str]) -> UserRole:
    if not groups:
        return UserRole.PATIENT
    return UserRole.from_group_name(groups[0])
