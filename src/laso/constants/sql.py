"""SQL query constants — all database queries in one readable location."""


class QuizSQL:
    INSERT = """
        INSERT INTO quiz_submissions (
            quiz_id, age, gender, height_cm, weight_kg,
            conditions, current_medications, symptoms,
            activity_level, diet_type, sleep_hours, stress_level,
            primary_goal, target_weight_kg, timeline_weeks,
            readiness_score, main_concern, bmi, eligible
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    GET_BY_ID = "SELECT * FROM quiz_submissions WHERE quiz_id = %s"


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
