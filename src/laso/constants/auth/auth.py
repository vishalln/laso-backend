"""Auth domain constants — error messages, field keys, env vars."""

from dataclasses import dataclass
from typing import Final

from laso.enums import UserRole


DEFAULT_USER_ROLE: Final[UserRole] = UserRole.PATIENT


@dataclass(frozen=True)
class AuthConstants:
    ERROR_NO_TOKEN: Final[str] = "Authentication required"
    ERROR_INVALID_TOKEN: Final[str] = "Invalid or expired token"
    ERROR_UNAUTHORIZED: Final[str] = "Incorrect email or password"
    ERROR_USER_NOT_FOUND: Final[str] = "No account found with this email"
    ERROR_USER_NOT_CONFIRMED: Final[str] = "Please verify your email address"
    ERROR_AUTH_FAILED: Final[str] = "Authentication failed"
    ERROR_INVALID_REFRESH: Final[str] = "Invalid refresh token"
    
    ERROR_USERNAME_EXISTS: Final[str] = "An account with this email already exists"
    ERROR_INVALID_PASSWORD: Final[str] = "Password must be at least 8 characters with uppercase, lowercase, and digit"
    ERROR_SIGNUP_FAILED: Final[str] = "Signup failed"
    
    ERROR_ADMIN_ONLY: Final[str] = "Admin access required"
    ERROR_INVALID_ROLE: Final[str] = "Invalid role specified"
    ERROR_ROLE_UPDATE_FAILED: Final[str] = "Failed to update user role"
    ERROR_USER_UPDATE_FAILED: Final[str] = "Failed to update user"
    
    SUCCESS_ROLE_UPDATED: Final[str] = "User role updated successfully"
    SUCCESS_ACCOUNT_CREATED: Final[str] = "Account created successfully"


AUTH_ERRORS: Final[AuthConstants] = AuthConstants()


@dataclass(frozen=True)
class EnvironmentVariable:
    USER_POOL_ID: Final[str] = "USER_POOL_ID"
    APP_CLIENT_ID: Final[str] = "APP_CLIENT_ID"
    DB_SECRET_ARN: Final[str] = "DB_SECRET_ARN"
    AWS_REGION: Final[str] = "AWS_REGION"


ENV: Final[EnvironmentVariable] = EnvironmentVariable()


@dataclass(frozen=True)
class HttpHeader:
    CONTENT_TYPE: Final[str] = "Content-Type"
    AUTHORIZATION: Final[str] = "Authorization"
    ACCESS_CONTROL_ALLOW_ORIGIN: Final[str] = "Access-Control-Allow-Origin"
    ACCESS_CONTROL_ALLOW_HEADERS: Final[str] = "Access-Control-Allow-Headers"
    ACCESS_CONTROL_ALLOW_METHODS: Final[str] = "Access-Control-Allow-Methods"


HEADER: Final[HttpHeader] = HttpHeader()


@dataclass(frozen=True)
class HttpHeaderValue:
    JSON: Final[str] = "application/json"
    CORS_ORIGIN: Final[str] = "*"
    CORS_HEADERS: Final[str] = "Content-Type,Authorization"
    CORS_METHODS: Final[str] = "GET,PUT,POST,DELETE,OPTIONS"


HEADER_VALUE: Final[HttpHeaderValue] = HttpHeaderValue()


@dataclass(frozen=True)
class CognitoAttribute:
    EMAIL: Final[str] = "email"
    NAME: Final[str] = "name"
    SUB: Final[str] = "sub"
    EMAIL_VERIFIED: Final[str] = "email_verified"


COGNITO_ATTR: Final[CognitoAttribute] = CognitoAttribute()
