"""Runtime configuration, read from environment variables.

Every setting has a safe default so the service starts with no configuration.
The names match the operational runbook (docs/09-operational-runbook.md).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    db_path: str = "portflow.db"
    spool_dir: str = "spool"
    terminal_code: str = "BEZEE"
    pool_size: int = 10
    pool_timeout: float = 2.0
    db_retries: int = 3
    retry_backoff: float = 0.5
    spool_interval: float = 5.0
    # Re-introduces the connection leak fixed in 1.2.1 (PRB-001). Only for
    # reproducing INC-001 in a demo; never set this in a real environment.
    fault_leak_on_error: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=os.environ.get("PORTFLOW_DB", cls.db_path),
            spool_dir=os.environ.get("PORTFLOW_SPOOL_DIR", cls.spool_dir),
            terminal_code=os.environ.get("PORTFLOW_TERMINAL_CODE", cls.terminal_code),
            pool_size=int(os.environ.get("PORTFLOW_POOL_SIZE", cls.pool_size)),
            pool_timeout=float(os.environ.get("PORTFLOW_POOL_TIMEOUT", cls.pool_timeout)),
            db_retries=int(os.environ.get("PORTFLOW_DB_RETRIES", cls.db_retries)),
            retry_backoff=float(os.environ.get("PORTFLOW_RETRY_BACKOFF", cls.retry_backoff)),
            spool_interval=float(os.environ.get("PORTFLOW_SPOOL_INTERVAL", cls.spool_interval)),
            fault_leak_on_error=_env_bool("PORTFLOW_FAULT_LEAK_ON_ERROR", False),
        )
