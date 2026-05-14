"""Admin user status management service."""

import logging
import os

from laso.enums import UserStatus
from laso.exceptions import NotFoundError
from laso.models.patient import Patient
from laso.utils.cognito import CognitoClient
from laso.utils.db import execute, update_by_id

log = logging.getLogger(__name__)


def toggle_status(email: str, status: str) -> dict:
    """Toggle patient status and enable/disable Cognito account accordingly."""
    log.info("admin_user_service.toggle_status | email=%s status=%s", email, status)
    patient = Patient.get_by_email(email)
    if not patient:
        raise NotFoundError("Patient not found")

    previous_status = patient.status.value
    new_status = UserStatus(status)

    cognito = CognitoClient(
        user_pool_id=os.environ["USER_POOL_ID"],
        client_id=os.environ["APP_CLIENT_ID"],
    )

    if new_status in (UserStatus.INACTIVE, UserStatus.SUSPENDED):
        cognito.client.admin_disable_user(UserPoolId=cognito.user_pool_id, Username=email)
    elif new_status == UserStatus.ACTIVE:
        cognito.client.admin_enable_user(UserPoolId=cognito.user_pool_id, Username=email)

    update_by_id("patients", "patient_id", patient.patient_id, status=new_status.value)

    return {"email": email, "previous_status": previous_status, "new_status": new_status.value}


PATIENT_TABLES = [
    ("quiz_submissions", "patient_id"),
    ("weekly_check_ins", "patient_id"),
    ("messages", "conversation_id", "conversations", "patient_id"),
    ("conversations", "patient_id"),
    ("clinical_notes", "patient_id"),
    ("patient_flags", "patient_id"),
    ("treatment_plans", "patient_id"),
    ("payments", "patient_id"),
    ("orders", "patient_id"),
    ("prescriptions", "patient_id"),
    ("blood_tests", "patient_id"),
    ("consultations", "patient_id"),
    ("programme_steps", "programme_id", "programmes", "patient_id"),
    ("programmes", "patient_id"),
    ("tasks", "patient_id"),
]


def purge(email: str, cognito_client: CognitoClient) -> dict:
    log.info("admin_user_service.purge | email=%s", email)

    patient = Patient.get_by_email(email)
    deleted = {}

    if patient:
        pid = patient.patient_id

        for entry in PATIENT_TABLES:
            if len(entry) == 2:
                table, col = entry
                rows = execute(f"DELETE FROM {table} WHERE {col} = %s RETURNING 1", (pid,))
            else:
                table, fk_col, parent_table, parent_col = entry
                rows = execute(
                    f"DELETE FROM {table} WHERE {fk_col} IN "
                    f"(SELECT {fk_col} FROM {parent_table} WHERE {parent_col} = %s) RETURNING 1",
                    (pid,),
                )
            deleted[table] = len(rows)

        execute("DELETE FROM patients WHERE patient_id = %s", (pid,))
        deleted["patients"] = 1
        log.info("admin_user_service.purge | db_deleted=%s", deleted)

    cognito_client.delete_user(email)
    deleted["cognito"] = 1

    log.info("admin_user_service.purge | complete | email=%s", email)
    return deleted
