"""Program eligibility determination logic."""

from laso.constants.quiz import (
    BMI_THRESHOLD_STANDARD,
    BMI_THRESHOLD_COMORBIDITY,
    COMORBIDITIES,
)


def check_eligibility(bmi: float, conditions: list[str]) -> bool:
    """Determine if patient is eligible for weight management program.
    
    Eligibility criteria:
    1. BMI >= 30 (standard threshold), OR
    2. BMI >= 27 (with comorbidity threshold) AND has qualifying comorbidity
    
    Args:
        bmi: Patient's Body Mass Index
        conditions: List of patient's medical conditions
        
    Returns:
        True if eligible, False otherwise
    """
    # Check if patient meets standard BMI threshold
    if bmi >= BMI_THRESHOLD_STANDARD:
        return True
    
    # Check if patient has comorbidity AND meets lower BMI threshold
    has_qualifying_comorbidity = bool(COMORBIDITIES & set(conditions))
    if bmi >= BMI_THRESHOLD_COMORBIDITY and has_qualifying_comorbidity:
        return True
    
    return False
