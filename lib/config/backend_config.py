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


# ── Singletons consumed by BackendStack / AdminStack ─────────────────────────
LAMBDA = LambdaConfig()
API    = ApiConfig()
