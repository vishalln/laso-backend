"""Auth CDK configuration — Cognito user pool, groups, app client settings."""

from dataclasses import dataclass, field
from aws_cdk import Duration
from typing import Final, List, Dict
from src.laso.constants.oauth import OAuthConfig


@dataclass(frozen=True)
class UserPoolConfig:
    pool_name: str = "laso-user-pool"
    self_sign_up_enabled: bool = True
    min_password_length: int = 8
    require_lowercase: bool = True
    require_uppercase: bool = True
    require_digits: bool = True
    require_symbols: bool = False
    access_token_validity_hours: int = 1
    id_token_validity_hours: int = 1
    refresh_token_validity_days: int = 30


@dataclass(frozen=True)
class UserGroupConfig:
    name: str
    description: str
    precedence: int


@dataclass(frozen=True)
class UserGroupsConfig:
    PATIENT: UserGroupConfig = UserGroupConfig(
        name="Patient",
        description="Patients managing their health journey",
        precedence=4
    )
    DOCTOR: UserGroupConfig = UserGroupConfig(
        name="Doctor",
        description="Doctors viewing patient panels",
        precedence=3
    )
    COORDINATOR: UserGroupConfig = UserGroupConfig(
        name="Coordinator",
        description="Care coordinators managing queues",
        precedence=2
    )
    ADMIN: UserGroupConfig = UserGroupConfig(
        name="Admin",
        description="Administrators with full access",
        precedence=1
    )


@dataclass(frozen=True)
class OAuthProviderConfig:
    enabled: bool = True
    domain_prefix: str = OAuthConfig.COGNITO_DOMAIN_PREFIX
    google_client_id: str = OAuthConfig.GOOGLE_CLIENT_ID
    google_scopes: List[str] = field(default_factory=lambda: OAuthConfig.GOOGLE_SCOPES)
    callback_urls: List[str] = field(default_factory=lambda: list(OAuthConfig.CALLBACK_URLS.values()))
    logout_urls: List[str] = field(default_factory=lambda: list(OAuthConfig.LOGOUT_URLS.values()))
    allowed_flows: List[str] = field(default_factory=lambda: OAuthConfig.OAUTH_FLOWS)
    allowed_scopes: List[str] = field(default_factory=lambda: OAuthConfig.OAUTH_SCOPES)
    attribute_mapping: Dict[str, str] = field(default_factory=lambda: OAuthConfig.ATTRIBUTE_MAPPING)
    secret_name: str = OAuthConfig.SECRET_NAME


USER_POOL: Final[UserPoolConfig] = UserPoolConfig()
USER_GROUPS: Final[UserGroupsConfig] = UserGroupsConfig()
OAUTH: Final[OAuthProviderConfig] = OAuthProviderConfig()
