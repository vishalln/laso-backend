"""Analytics service — SQL aggregations for admin dashboard."""

import logging

from laso.utils.db import execute

log = logging.getLogger(__name__)


def overview() -> dict:
    log.info("analytics_service.overview")
    row = execute("""
        SELECT
            (SELECT COUNT(*) FROM patients) as total_patients,
            (SELECT COUNT(*) FROM patients WHERE status = 'active') as active_patients,
            (SELECT COALESCE(AVG(
                CASE WHEN doses_scheduled > 0
                     THEN (doses_taken::FLOAT / doses_scheduled) * 100
                     ELSE 0
                END), 0)
             FROM weekly_check_ins WHERE doses_scheduled > 0) as avg_adherence,
            (SELECT COALESCE(AVG(first_weight - last_weight), 0)
             FROM (
                SELECT DISTINCT ON (patient_id)
                    FIRST_VALUE(weight_kg) OVER w as first_weight,
                    LAST_VALUE(weight_kg) OVER w as last_weight
                FROM weekly_check_ins
                WHERE weight_kg IS NOT NULL
                WINDOW w AS (PARTITION BY patient_id ORDER BY submitted_at
                             ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
             ) sub
             WHERE first_weight > last_weight
            ) as avg_weight_lost
    """)
    log.info("analytics_service.overview | result=%s", row)
    return row[0] if row else {}


def enrolment_trend() -> list:
    log.info("analytics_service.enrolment_trend")
    rows = execute("""
        SELECT TO_CHAR(created_at, 'YYYY-MM') as label, COUNT(*) as value
        FROM programmes
        WHERE created_at >= NOW() - INTERVAL '12 months'
        GROUP BY TO_CHAR(created_at, 'YYYY-MM')
        ORDER BY label
    """)
    log.info("analytics_service.enrolment_trend | rows=%d", len(rows))
    return rows


def weight_by_week() -> list:
    log.info("analytics_service.weight_by_week")
    rows = execute("""
        WITH weekly AS (
            SELECT
                ci.week_number as week_num,
                ci.weight_kg - LAG(ci.weight_kg) OVER (
                    PARTITION BY ci.patient_id ORDER BY ci.submitted_at
                ) as delta
            FROM weekly_check_ins ci
            JOIN programmes p ON p.patient_id = ci.patient_id AND p.status = 'active'
            WHERE ci.weight_kg IS NOT NULL
        )
        SELECT week_num as label, COALESCE(AVG(delta), 0) as value
        FROM weekly
        WHERE week_num >= 0
        GROUP BY week_num
        ORDER BY week_num
    """)
    log.info("analytics_service.weight_by_week | rows=%d", len(rows))
    return rows


def adherence_trend() -> list:
    log.info("analytics_service.adherence_trend")
    rows = execute("""
        SELECT TO_CHAR(DATE_TRUNC('week', submitted_at), 'YYYY-MM-DD') as label,
               AVG(CASE WHEN doses_scheduled > 0
                        THEN (doses_taken::FLOAT / doses_scheduled) * 100
                        ELSE 0 END) as value
        FROM weekly_check_ins
        WHERE submitted_at >= NOW() - INTERVAL '12 weeks' AND doses_scheduled > 0
        GROUP BY DATE_TRUNC('week', submitted_at)
        ORDER BY label
    """)
    log.info("analytics_service.adherence_trend | rows=%d", len(rows))
    return rows


def status_distribution() -> list:
    log.info("analytics_service.status_distribution")
    rows = execute("""
        SELECT status as label, COUNT(*) as value
        FROM patients
        GROUP BY status
        ORDER BY value DESC
    """)
    log.info("analytics_service.status_distribution | rows=%d", len(rows))
    return rows


def glucose_trend() -> list:
    log.info("analytics_service.glucose_trend")
    rows = execute("""
        SELECT TO_CHAR(DATE_TRUNC('week', submitted_at), 'YYYY-MM-DD') as label,
               AVG(fasting_glucose) as value
        FROM weekly_check_ins
        WHERE submitted_at >= NOW() - INTERVAL '12 weeks' AND fasting_glucose IS NOT NULL
        GROUP BY DATE_TRUNC('week', submitted_at)
        ORDER BY label
    """)
    log.info("analytics_service.glucose_trend | rows=%d", len(rows))
    return rows


def side_effects_top() -> list:
    log.info("analytics_service.side_effects_top")
    rows = execute("""
        SELECT elem->>'symptom' as label, COUNT(*) as value
        FROM weekly_check_ins, jsonb_array_elements(side_effects) as elem
        WHERE side_effects IS NOT NULL AND side_effects != '[]'::JSONB
        GROUP BY elem->>'symptom'
        ORDER BY value DESC
        LIMIT 8
    """)
    log.info("analytics_service.side_effects_top | rows=%d", len(rows))
    return rows
