"""Single retry decorator — exponential backoff, resets DB connection on failure."""

import functools
import logging
import time

import psycopg2

log = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (
    psycopg2.OperationalError,
    psycopg2.InterfaceError,
    ConnectionError,
    TimeoutError,
)


def with_retry(max_attempts: int = 3, backoff_base_ms: int = 200):
    """Retry decorator with exponential backoff. Resets DB connection between retries."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        delay_ms = backoff_base_ms * (2 ** (attempt - 1))
                        log.warning(
                            "with_retry | fn=%s attempt=%d/%d error=%s backoff_ms=%d",
                            fn.__name__, attempt, max_attempts, str(exc), delay_ms,
                        )
                        _reset_connection()
                        time.sleep(delay_ms / 1000.0)
                    else:
                        log.error(
                            "with_retry | fn=%s exhausted attempts=%d error=%s",
                            fn.__name__, max_attempts, str(exc),
                        )
            raise last_exc
        return wrapper
    return decorator


def _reset_connection() -> None:
    """Force-close the cached DB connection so next call creates a fresh one."""
    import laso.utils.db as db_module
    if db_module._connection:
        try:
            db_module._connection.close()
        except Exception:
            pass
        db_module._connection = None
