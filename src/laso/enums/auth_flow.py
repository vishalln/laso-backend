"""Cognito authentication flow enumeration."""

from enum import Enum


class AuthFlow(str, Enum):
    USER_PASSWORD_AUTH = "USER_PASSWORD_AUTH"
    USER_SRP_AUTH = "USER_SRP_AUTH"
    REFRESH_TOKEN_AUTH = "REFRESH_TOKEN_AUTH"
    CUSTOM_AUTH = "CUSTOM_AUTH"
