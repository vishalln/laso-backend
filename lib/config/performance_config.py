"""Performance thresholds and limits — rate limits, timeouts, pagination."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitoPerformance:
    timeout_seconds: int = 30
    max_retries: int = 3
    token_expiry_hours: int = 1
    refresh_token_expiry_days: int = 30


@dataclass(frozen=True)
class DynamoPerformance:
    batch_size: int = 25
    page_size: int = 20
    query_timeout_seconds: int = 10


@dataclass(frozen=True)
class ApiPerformance:
    rate_limit_per_minute: int = 100
    burst_limit: int = 200
    timeout_seconds: int = 30


@dataclass(frozen=True)
class LambdaPerformance:
    memory_mb: int = 512
    timeout_seconds: int = 30
    reserved_concurrent_executions: int = 10


@dataclass(frozen=True)
class GoogleCalendarPerformance:
    timeout_seconds: int = 10
    max_retries: int = 3
    default_duration_minutes: int = 30


@dataclass(frozen=True)
class DbRetryPerformance:
    max_attempts: int = 3
    backoff_base_ms: int = 200


@dataclass(frozen=True)
class PaginationPerformance:
    default_limit: int = 20
    max_limit: int = 100


COGNITO = CognitoPerformance()
DYNAMO = DynamoPerformance()
API = ApiPerformance()
LAMBDA = LambdaPerformance()
GOOGLE_CALENDAR = GoogleCalendarPerformance()
DB_RETRY = DbRetryPerformance()
PAGINATION = PaginationPerformance()
