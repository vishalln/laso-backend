"""Quiz submission handler — orchestrates BMI, eligibility, and persistence."""

import json
import logging

from laso.models.quiz import QuizSubmission
from laso.utils.health_metrics import calculate_bmi
from laso.utils.eligibility import check_eligibility

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def submit_quiz(data: dict) -> dict:
    """Parse → compute → persist → respond."""
    log.info("submit_quiz | request=%s", data)

    submission = QuizSubmission.from_dict(data)

    if submission.weight_kg and submission.height_cm:
        submission.bmi = calculate_bmi(submission.weight_kg, submission.height_cm)
        submission.eligible = check_eligibility(submission.bmi, submission.conditions)

    submission.save()

    result = {"quiz_id": submission.quiz_id, "bmi": submission.bmi, "eligible": submission.eligible}
    log.info("submit_quiz | result=%s", result)
    return result


def lambda_handler(event: dict, context) -> dict:
    """Lambda entry point for API Gateway."""
    log.info("quiz_handler | event=%s", event)

    try:
        body = json.loads(event.get("body", "{}"))
        result = submit_quiz(body)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
            },
            "body": json.dumps(result),
        }
    except Exception as e:
        log.exception("quiz_handler | error processing submission")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
