"""Quiz service — submission, eligibility assessment, retrieval."""

import logging
from typing import Dict, Optional

from laso.constants.quiz import BMI_THRESHOLD_COMORBIDITY, BMI_THRESHOLD_STANDARD, COMORBIDITIES
from laso.exceptions import ConflictError, NotFoundError
from laso.models.quiz import QuizSubmission

log = logging.getLogger(__name__)


def submit(patient_id: Optional[str], data: Dict) -> Dict:
    log.info("quiz_service.submit | patient_id=%s", patient_id)

    submission = QuizSubmission.from_dict(data)
    submission.patient_id = patient_id

    if submission.height_cm and submission.weight_kg:
        submission.bmi = round(submission.weight_kg / (submission.height_cm / 100) ** 2, 1)

    submission.eligible = _assess_eligibility(submission)

    submission.save()
    log.info("quiz_service.submit | success | quiz_id=%s eligible=%s bmi=%s", submission.quiz_id, submission.eligible, submission.bmi)
    return submission.to_dict()


def get_latest(patient_id: str) -> Dict:
    log.info("quiz_service.get_latest | patient_id=%s", patient_id)

    submission = QuizSubmission.get_latest_by_patient(patient_id)
    if not submission:
        raise NotFoundError("No quiz submission found")

    log.info("quiz_service.get_latest | found | quiz_id=%s", submission.quiz_id)
    return submission.to_dict()


def claim(quiz_id: str, patient_id: str) -> Dict:
    log.info("quiz_service.claim | quiz_id=%s patient_id=%s", quiz_id, patient_id)

    submission = QuizSubmission.get_by_id(quiz_id)
    if not submission:
        raise NotFoundError("Quiz submission not found")

    if submission.patient_id is not None:
        raise ConflictError("Quiz submission has already been claimed")

    submission.claim(patient_id)
    log.info("quiz_service.claim | success | quiz_id=%s", quiz_id)
    return submission.to_dict()


def _assess_eligibility(submission: QuizSubmission) -> bool:
    if not submission.bmi:
        return False

    if submission.bmi >= BMI_THRESHOLD_STANDARD:
        return True

    if submission.bmi >= BMI_THRESHOLD_COMORBIDITY:
        return any(c in COMORBIDITIES for c in (submission.conditions or []))

    return False
