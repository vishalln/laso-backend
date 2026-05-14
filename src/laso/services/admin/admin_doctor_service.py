"""Admin doctor management service."""

import logging
import os
from datetime import datetime, timedelta, time
from uuid import uuid4

from laso.enums import DoctorSpecialisation
from laso.exceptions import ConflictError, NotFoundError
from laso.models.doctor import Doctor, DoctorWorkingHours
from laso.models.consultation import Consultation
from laso.models.patient import Patient
from laso.utils.cognito import CognitoClient
from laso.utils.db import execute, update_by_id

log = logging.getLogger(__name__)


def _cognito():
    return CognitoClient(
        user_pool_id=os.environ["USER_POOL_ID"],
        client_id=os.environ["APP_CLIENT_ID"],
    )


def create(body: dict) -> dict:
    log.info("admin_doctor_service.create | email=%s", body.get("email"))
    from laso.utils.validation import validate_required
    validate_required(body, ["email", "name"])

    cognito = _cognito()
    doctor_id = cognito.admin_create_user(
        email=body["email"],
        name=body["name"],
        group="Doctor",
    )

    if body.get("password"):
        cognito.admin_set_password(body["email"], body["password"])

    doctor = Doctor(
        doctor_id=doctor_id,
        email=body["email"],
        name=body["name"],
        specialisation=DoctorSpecialisation(body.get("specialisation", "general_medicine")),
        phone=body.get("phone"),
    )
    doctor.save()

    for day in range(7):
        wh = DoctorWorkingHours(
            id=str(uuid4()),
            doctor_id=doctor_id,
            day_of_week=day,
            is_working=day < 5,
            start_time=time(9, 0) if day < 5 else None,
            end_time=time(17, 0) if day < 5 else None,
        )
        wh.save()

    log.info("admin_doctor_service.create | success | doctor_id=%s", doctor_id)
    return doctor.to_dict()


def update(doctor_id: str, body: dict) -> dict:
    """Update name, specialisation, phone, working hours."""
    log.info("admin_doctor_service.update | doctor_id=%s", doctor_id)
    doctor = Doctor.get_by_id(doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")

    allowed = {"name", "specialisation", "phone"}
    fields = {k: v for k, v in body.items() if k in allowed}
    if fields:
        update_by_id("doctors", "doctor_id", doctor_id, **fields)

    if "working_hours" in body:
        for wh_data in body["working_hours"]:
            update_by_id("doctor_working_hours", "id", wh_data["id"],
                         is_working=wh_data.get("is_working", True),
                         start_time=wh_data.get("start_time"),
                         end_time=wh_data.get("end_time"))

    return Doctor.get_by_id(doctor_id).to_dict()


def toggle_status(doctor_id: str, status: str) -> dict:
    """Activate or deactivate a doctor."""
    log.info("admin_doctor_service.toggle_status | doctor_id=%s status=%s", doctor_id, status)
    doctor = Doctor.get_by_id(doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")
    update_by_id("doctors", "doctor_id", doctor_id, status=status)
    return {**doctor.to_dict(), "status": status}


def delete(doctor_id: str) -> dict:
    """Delete doctor after verifying no active patients or upcoming consultations."""
    log.info("admin_doctor_service.delete | doctor_id=%s", doctor_id)
    doctor = Doctor.get_by_id(doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")

    active_patients = execute(
        "SELECT COUNT(*) as cnt FROM patients WHERE assigned_doctor_id = %s AND status = 'active'",
        (doctor_id,),
    )
    if active_patients and active_patients[0]["cnt"] > 0:
        raise ConflictError("Doctor has active patients")

    upcoming = execute(
        "SELECT COUNT(*) as cnt FROM consultations WHERE doctor_id = %s AND scheduled_at > NOW() AND status != 'cancelled'",
        (doctor_id,),
    )
    if upcoming and upcoming[0]["cnt"] > 0:
        raise ConflictError("Doctor has upcoming consultations")

    execute("DELETE FROM doctor_working_hours WHERE doctor_id = %s", (doctor_id,))
    execute("DELETE FROM doctors WHERE doctor_id = %s", (doctor_id,))
    return {"deleted": True, "doctor_id": doctor_id}


def list_all() -> list:
    """List all doctors."""
    log.info("admin_doctor_service.list_all")
    return [d.to_dict() for d in Doctor.list_all()]


def get_availability(doctor_id: str) -> dict:
    """Return working hours + booked slots for next 7 days."""
    log.info("admin_doctor_service.get_availability | doctor_id=%s", doctor_id)
    doctor = Doctor.get_by_id(doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")

    working_hours = [
        {"day_of_week": wh.day_of_week, "is_working": wh.is_working,
         "start_time": wh.start_time.isoformat() if wh.start_time else None,
         "end_time": wh.end_time.isoformat() if wh.end_time else None}
        for wh in DoctorWorkingHours.get_for_doctor(doctor_id)
    ]

    now = datetime.utcnow()
    end = now + timedelta(days=7)
    booked = execute(
        "SELECT scheduled_at, duration_minutes FROM consultations WHERE doctor_id = %s AND scheduled_at BETWEEN %s AND %s AND status != 'cancelled'",
        (doctor_id, now, end),
    )
    booked_slots = [
        {"scheduled_at": r["scheduled_at"].isoformat() if r["scheduled_at"] else None,
         "duration_minutes": r["duration_minutes"]}
        for r in booked
    ]

    return {"working_hours": working_hours, "booked_slots": booked_slots}
