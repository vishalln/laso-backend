"""Cognito error code enumeration."""

from enum import Enum


class CognitoErrorCode(str, Enum):
    NOT_AUTHORIZED = "NotAuthorizedException"
    USER_NOT_FOUND = "UserNotFoundException"
    USER_NOT_CONFIRMED = "UserNotConfirmedException"
    USERNAME_EXISTS = "UsernameExistsException"
    INVALID_PASSWORD = "InvalidPasswordException"
    INVALID_PARAMETER = "InvalidParameterException"
    CODE_MISMATCH = "CodeMismatchException"
    EXPIRED_CODE = "ExpiredCodeException"
