"""User role enumeration."""

from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    COORDINATOR = "coordinator"
    ADMIN = "admin"
    
    @property
    def group_name(self) -> str:
        return self.value.capitalize()
    
    @property
    def precedence(self) -> int:
        precedence_map = {
            UserRole.ADMIN: 1,
            UserRole.COORDINATOR: 2,
            UserRole.DOCTOR: 3,
            UserRole.PATIENT: 4
        }
        return precedence_map[self]
    
    @property
    def description(self) -> str:
        descriptions = {
            UserRole.PATIENT: "Patients managing their health journey",
            UserRole.DOCTOR: "Doctors viewing patient panels",
            UserRole.COORDINATOR: "Care coordinators managing queues",
            UserRole.ADMIN: "Administrators with full access"
        }
        return descriptions[self]
    
    @classmethod
    def from_group_name(cls, group_name: str) -> "UserRole":
        for role in cls:
            if role.group_name == group_name:
                return role
        return cls.PATIENT
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value.lower() in [role.value for role in cls]
