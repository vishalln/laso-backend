"""Health and fitness metric calculations."""


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index from weight and height.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        
    Returns:
        BMI rounded to 1 decimal place
        
    Formula:
        BMI = weight (kg) / [height (m)]²
    """
    height_meters = height_cm / 100
    bmi = weight_kg / (height_meters ** 2)
    return round(bmi, 1)


def classify_bmi(bmi: float) -> str:
    """Classify BMI into standard WHO categories.
    
    Args:
        bmi: Body Mass Index value
        
    Returns:
        Classification string: underweight, normal, overweight, or obese
    """
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"
