"""Catalog domain enumerations."""

from enum import Enum


class ProductCategory(str, Enum):
    MEDICATION = "medication"
    SUPPLEMENT = "supplement"
    DEVICE = "device"


class DoctorSpecialisation(str, Enum):
    GENERAL_MEDICINE = "general_medicine"
    ENDOCRINOLOGY = "endocrinology"
    BARIATRICS = "bariatrics"
    INTERNAL_MEDICINE = "internal_medicine"
    OTHER = "other"
