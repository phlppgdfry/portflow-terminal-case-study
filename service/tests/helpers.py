import json
import logging
import tempfile
from pathlib import Path

from portflow import db
from portflow.config import Settings
from portflow.service import ManifestService, Spool

SAMPLES = Path(__file__).resolve().parents[2] / "integrations"
logging.getLogger("portflow").setLevel(logging.CRITICAL)


def sample(name: str) -> str:
    return (SAMPLES / name).read_text()


def manifest_json(**overrides) -> str:
    payload = json.loads(sample("sample-vehicle-import.json"))
    payload.update(overrides)
    return json.dumps(payload)


class Env:
    """A service on a throwaway database. Retries are fast so tests stay quick."""

    def __init__(self, pool_size: int = 3, leak_on_error: bool = False, retries: int = 1):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.settings = Settings(
            db_path=str(base / "test.db"),
            spool_dir=str(base / "spool"),
            pool_size=pool_size,
            pool_timeout=0.05,
            db_retries=retries,
            retry_backoff=0,
            fault_leak_on_error=leak_on_error,
        )
        db.init_schema(self.settings.db_path)
        self.pool = db.ConnectionPool(self.settings.db_path, pool_size, 0.05, leak_on_error)
        self.spool = Spool(self.settings.spool_dir)
        self.service = ManifestService(self.settings, self.pool, self.spool)

    def close(self) -> None:
        self.pool.close()
        self.tmp.cleanup()
