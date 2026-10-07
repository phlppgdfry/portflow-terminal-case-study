"""Message processing: parse -> validate -> persist, with retry and a durable spool.

Log events (MESSAGE_RECEIVED, VALIDATION_SUCCESS, DATABASE_TIMEOUT, RETRY_n,
MESSAGE_PENDING, ...) are the ones the runbook and incident records refer to.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from . import db
from .config import Settings
from .edi import from_edi
from .mapping import PayloadSyntaxError, from_json
from .model import Issue, Manifest
from .validation import validate

log = logging.getLogger("portflow")


class DatabaseUnavailable(Exception):
    """All retries failed; the message must wait in the spool."""


@dataclass
class Outcome:
    status: str  # ACCEPTED | REJECTED | DUPLICATE | PENDING
    message_id: int | None = None
    errors: list[Issue] = field(default_factory=list)

    @property
    def http_status(self) -> int:
        return {"ACCEPTED": 201, "REJECTED": 422, "DUPLICATE": 200, "PENDING": 202}[self.status]

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "messageId": self.message_id,
            "errors": [e.as_dict() for e in self.errors],
        }


class Spool:
    """Messages that could not be stored wait here as files until the database is back."""

    def __init__(self, directory: str):
        self.path = Path(directory)
        self.path.mkdir(parents=True, exist_ok=True)

    def put(self, raw: str, channel: str, received_at: str) -> Path:
        name = f"{received_at.replace(':', '')}-{uuid.uuid4().hex[:8]}.json"
        target = self.path / name
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps({"raw": raw, "channel": channel, "receivedAt": received_at}))
        tmp.replace(target)  # atomic: a half-written file is never picked up
        return target

    def items(self) -> list[Path]:
        return sorted(self.path.glob("*.json"))

    def __len__(self) -> int:
        return len(self.items())


class ManifestService:
    def __init__(self, settings: Settings, pool: db.ConnectionPool, spool: Spool):
        self.settings = settings
        self.pool = pool
        self.spool = spool

    def submit(self, raw: str, channel: str) -> Outcome:
        received_at = db.now()
        try:
            return self._process(raw, channel, received_at)
        except DatabaseUnavailable:
            self.spool.put(raw, channel, received_at)
            log.error("MESSAGE_PENDING channel=%s backlog=%d", channel, len(self.spool))
            return Outcome("PENDING")

    def drain_spool(self) -> int:
        """Reprocess spooled messages in arrival order; stop at the first database failure."""
        recovered = 0
        for item in self.spool.items():
            data = json.loads(item.read_text())
            try:
                outcome = self._process(data["raw"], data["channel"], data["receivedAt"])
            except DatabaseUnavailable:
                break
            item.unlink()
            recovered += 1
            log.info("MESSAGE_RECOVERED status=%s id=%s", outcome.status, outcome.message_id)
        return recovered

    # -- internals ----------------------------------------------------------

    def _process(self, raw: str, channel: str, received_at: str) -> Outcome:
        try:
            manifest, issues = from_json(raw) if channel == "REST" else from_edi(raw)
        except PayloadSyntaxError as exc:
            manifest, issues = Manifest(channel=channel), [Issue("E-SYNTAX", "payload", str(exc))]
            log.warning("MESSAGE_RECEIVED channel=%s partner=? ref=? bytes=%d", channel, len(raw))
        else:
            log.info(
                "MESSAGE_RECEIVED channel=%s partner=%s ref=%s vehicles=%d",
                channel, manifest.partner_id, manifest.message_ref, len(manifest.vehicles),
            )
            issues += validate(manifest, self.settings.terminal_code, issues)

        if issues:
            log.warning("VALIDATION_FAILED codes=%s", ",".join(sorted({i.code for i in issues})))
        else:
            log.info("VALIDATION_SUCCESS shipment=%s", manifest.shipment_ref)

        return self._with_retry(lambda: self._store(manifest, raw, received_at, issues))

    def _with_retry(self, unit_of_work) -> Outcome:
        attempts = self.settings.db_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return unit_of_work()
            except (db.PoolTimeout, sqlite3.OperationalError) as exc:
                log.error("DATABASE_TIMEOUT attempt=%d/%d reason=%s", attempt, attempts, exc)
                if attempt < attempts:
                    log.warning("RETRY_%d", attempt)
                    time.sleep(self.settings.retry_backoff * attempt)
        raise DatabaseUnavailable()

    def _store(self, manifest: Manifest, raw: str, received_at: str, issues: list[Issue]) -> Outcome:
        try:
            return self._store_once(manifest, raw, received_at, issues)
        except sqlite3.IntegrityError:
            # The unique key on (partner, shipment_ref) rejected the insert:
            # this shipment was already announced by an earlier message.
            log.warning("SHIPMENT_CONFLICT partner=%s shipment=%s", manifest.partner_id, manifest.shipment_ref)
            conflict = Issue(
                "V-SHIPMENT-EXISTS", "shipmentId", f"shipment {manifest.shipment_ref} was already announced"
            )
            return self._store_once(manifest, raw, received_at, issues + [conflict])

    def _store_once(self, manifest: Manifest, raw: str, received_at: str, issues: list[Issue]) -> Outcome:
        with self.pool.connection() as conn:
            if manifest.partner_id and manifest.message_ref:
                existing = db.find_message(conn, manifest.partner_id, manifest.message_ref)
                if existing is not None:
                    log.info("MESSAGE_DUPLICATE ref=%s original=%d", manifest.message_ref, existing["message_id"])
                    return Outcome("DUPLICATE", existing["message_id"])

            issues = issues + self._partner_issues(conn, manifest)
            if issues:
                message_id = db.insert_message(conn, manifest, raw, "REJECTED", received_at, issues)
                log.warning("MESSAGE_REJECTED id=%d codes=%s", message_id, ",".join(i.code for i in issues))
                return Outcome("REJECTED", message_id, issues)

            message_id = db.insert_message(conn, manifest, raw, "ACCEPTED", received_at, [])
            db.insert_shipment(conn, manifest, message_id)
            log.info("MESSAGE_ACCEPTED id=%d shipment=%s", message_id, manifest.shipment_ref)
            return Outcome("ACCEPTED", message_id)

    @staticmethod
    def _partner_issues(conn: sqlite3.Connection, manifest: Manifest) -> list[Issue]:
        if not manifest.partner_id:
            return []
        partner = db.get_partner(conn, manifest.partner_id)
        if partner is None:
            return [Issue("V-PARTNER-UNKNOWN", "partnerId", f"partner '{manifest.partner_id}' is not registered")]
        if partner["status"] != "ACTIVE":
            return [Issue("V-PARTNER-INACTIVE", "partnerId", f"partner status is {partner['status']}")]
        if partner["channel"] not in (manifest.channel, "BOTH"):
            return [
                Issue("V-PARTNER-CHANNEL", "partnerId", f"partner is set up for {partner['channel']}, not {manifest.channel}")
            ]
        return []
