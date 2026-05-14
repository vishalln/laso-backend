"""SQL constants — clinical domain (consultations)."""


class ConsultationSQL:
    INSERT = """
        INSERT INTO consultations (
            consultation_id, patient_id, doctor_id, programme_id,
            programme_step_id, type, duration_minutes, status,
            scheduled_at, meet_link, cancel_reason
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    GET_BY_ID = "SELECT * FROM consultations WHERE consultation_id = %s"

    LIST_FOR_PATIENT = """
        SELECT * FROM consultations
        WHERE patient_id = %s
        ORDER BY created_at DESC
    """

    LIST_FOR_DOCTOR = """
        SELECT * FROM consultations
        WHERE doctor_id = %s
        ORDER BY scheduled_at DESC
    """

    GET_FOR_DATE = """
        SELECT * FROM consultations
        WHERE doctor_id = %s AND DATE(scheduled_at) = %s
        ORDER BY scheduled_at
    """

    GET_UPCOMING_FOR_DOCTOR = """
        SELECT * FROM consultations
        WHERE doctor_id = %s AND scheduled_at > %s
        ORDER BY scheduled_at
    """

    GET_UPCOMING_FOR_PATIENT = """
        SELECT * FROM consultations
        WHERE patient_id = %s AND scheduled_at > %s AND status = 'scheduled'
        ORDER BY scheduled_at
    """

    UPDATE_SCHEDULE = """
        UPDATE consultations
        SET status='scheduled', doctor_id=%s, scheduled_at=%s, updated_at=NOW()
        WHERE consultation_id=%s
    """

    UPDATE_MEET_LINK = """
        UPDATE consultations
        SET meet_link=%s, updated_at=NOW()
        WHERE consultation_id=%s
    """

    UPDATE_STATUS = """
        UPDATE consultations
        SET status=%s, cancel_reason=%s, updated_at=NOW()
        WHERE consultation_id=%s
    """
