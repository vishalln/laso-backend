"""SQL constants — patient intake domain (quiz submissions, role audit)."""


class QuizSQL:
    INSERT = """
        INSERT INTO quiz_submissions (
            quiz_id, patient_id, age, gender, height_cm, weight_kg,
            conditions, current_medications, symptoms,
            activity_level, diet_type, sleep_hours, stress_level,
            primary_goal, target_weight_kg, timeline_weeks,
            readiness_score, main_concern, bmi, eligible
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    GET_BY_ID = "SELECT * FROM quiz_submissions WHERE quiz_id = %s"

    GET_LATEST_BY_PATIENT = """
        SELECT * FROM quiz_submissions
        WHERE patient_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """

    CLAIM = """
        UPDATE quiz_submissions
        SET patient_id = %s
        WHERE quiz_id = %s AND patient_id IS NULL
        RETURNING quiz_id
    """


class AuditSQL:
    INSERT = """
        INSERT INTO role_audit (
            audit_id, target_user_email, previous_role, new_role,
            changed_by_admin_email, changed_by_admin_id
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """

    GET_BY_EMAIL = """
        SELECT * FROM role_audit
        WHERE target_user_email = %s
        ORDER BY changed_at DESC
    """
