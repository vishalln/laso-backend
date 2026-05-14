"""CDK-level performance & infrastructure configuration — no magic numbers in stacks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LambdaConfig:
    timeout_seconds: int = 30
    memory_mb:       int = 256


@dataclass(frozen=True)
class ApiConfig:
    stage_name:      str = "prod"
    throttle_rps:    int = 100   # requests/sec per route
    throttle_burst:  int = 200


@dataclass(frozen=True)
class CronConfig:
    missed_checkin_schedule: str = "30 19 ? * SUN *"
    task_archiver_schedule:  str = "30 20 * * ? *"
    consult_status_schedule: str = "rate(5 minutes)"


# ── Singletons consumed by ApiStack / CronStack ──────────────────────────────
LAMBDA = LambdaConfig()
API    = ApiConfig()
CRON   = CronConfig()
