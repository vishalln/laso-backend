"""Blood test reference ranges — normal, borderline, high thresholds."""

from typing import Final

# Each entry: {"normal": (min, max), "borderline": (min, max), "high": (min, None)}
# Gender-specific entries use nested dicts: {"male": {...}, "female": {...}}

REFERENCE_RANGES: Final[dict] = {
    "hba1c": {
        "unit": "%",
        "normal": (0, 5.6),
        "borderline": (5.7, 6.4),
        "high": (6.5, None),
    },
    "fasting_glucose": {
        "unit": "mg/dL",
        "normal": (70, 99),
        "borderline": (100, 125),
        "high": (126, None),
    },
    "total_cholesterol": {
        "unit": "mg/dL",
        "normal": (0, 199),
        "borderline": (200, 239),
        "high": (240, None),
    },
    "ldl": {
        "unit": "mg/dL",
        "normal": (0, 99),
        "borderline": (100, 159),
        "high": (160, None),
    },
    "hdl": {
        "unit": "mg/dL",
        "male": {
            "normal": (40, None),
            "borderline": (35, 39),
            "low": (0, 34),
        },
        "female": {
            "normal": (50, None),
            "borderline": (45, 49),
            "low": (0, 44),
        },
    },
    "triglycerides": {
        "unit": "mg/dL",
        "normal": (0, 149),
        "borderline": (150, 199),
        "high": (200, None),
    },
    "alt": {
        "unit": "U/L",
        "normal": (7, 56),
        "borderline": (57, 80),
        "high": (81, None),
    },
    "ast": {
        "unit": "U/L",
        "normal": (10, 40),
        "borderline": (41, 60),
        "high": (61, None),
    },
    "creatinine": {
        "unit": "mg/dL",
        "male": {
            "normal": (0.7, 1.3),
            "borderline": (1.4, 1.6),
            "high": (1.7, None),
        },
        "female": {
            "normal": (0.6, 1.1),
            "borderline": (1.2, 1.4),
            "high": (1.5, None),
        },
    },
    "tsh": {
        "unit": "mIU/L",
        "normal": (0.4, 4.0),
        "borderline": (4.1, 6.0),
        "high": (6.1, None),
    },
}
