"""Database access: a bounded connection pool and the queries the service needs.

The demo runs on SQLite so it starts without infrastructure. The pool behaves
like an application-server datasource (JBoss/WildFly, max-pool-size +
blocking-timeout): when every connection is in use, callers wait and then fail
with DATABASE_TIMEOUT. That is exactly the failure in INC-001.
"""

from __future__ import annotations

import queue
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from importlib import resources
from typing import Iterator

from .mapping import TERMINAL_TZ
from .model import Issue, Manifest


class PoolTimeout(Exception):
    """No connection became available within the pool timeout."""


def now() -> str:
    return datetime.now(TERMINAL_TZ).strftime("%Y-%m-%dT%H:%M:%S")


def _connect(db_path: str, timeout: float) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=timeout, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(db_path: str) -> None:
    script = resources.files("portflow").joinpath("schema_sqlite.sql").read_text()
    conn = _connect(db_path, 5.0)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()


class ConnectionPool:
    def __init__(self, db_path: str, size: int, timeout: float, leak_on_error: bool = False):
        self.size = size
        self.timeout = timeout
        self.leak_on_error = leak_on_error
        self._free: queue.LifoQueue[sqlite3.Connection] = queue.LifoQueue()
        for _ in range(size):
            self._free.put(_connect(db_path, timeout))

    @property
    def available(self) -> int:
        return self._free.qsize()

    @contextmanager
    def connection(self, timeout: float | None = None) -> Iterator[sqlite3.Connection]:
        """Borrow a connection for one unit of work: commit on success, roll back on error.

        The connection always goes back to the pool, also on the error path.
        Version 1.2.0 skipped the release when the unit of work raised; that
        leak is what exhausted the pool in INC-001 (root cause in PRB-001).
        """
        try:
            conn = self._free.get(timeout=self.timeout if timeout is None else timeout)
        except queue.Empty:
            raise PoolTimeout(f"no connection available after {self.timeout}s") from None
        failed = False
        try:
            yield conn
            conn.commit()
        except BaseException:
            failed = True
            conn.rollback()
            raise
        finally:
            if not (failed and self.leak_on_error):
                self._free.put(conn)

    def close(self) -> None:
        while True:
            try:
                self._free.get_nowait().close()
            except queue.Empty:
                return


# --- queries ---------------------------------------------------------------


def find_message(conn: sqlite3.Connection, partner: str, ref: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT message_id, status FROM edi_message WHERE partner_code = ? AND message_ref = ?",
        (partner, ref),
    ).fetchone()


def get_partner(conn: sqlite3.Connection, partner_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT partner_id, channel, status FROM partner WHERE partner_id = ?", (partner_id,)
    ).fetchone()


def insert_message(
    conn: sqlite3.Connection,
    manifest: Manifest,
    raw: str,
    status: str,
    received_at: str,
    issues: list[Issue],
) -> int:
    cur = conn.execute(
        """INSERT INTO edi_message (partner_code, message_ref, channel, status, shipment_ref,
                                    vehicle_count, raw_payload, received_at, processed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            manifest.partner_id,
            manifest.message_ref,
            manifest.channel,
            status,
            manifest.shipment_ref,
            len(manifest.vehicles),
            raw,
            received_at,
            now(),
        ),
    )
    message_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO message_error (message_id, error_code, field_path, detail) VALUES (?, ?, ?, ?)",
        [(message_id, i.code, i.field, i.message) for i in issues],
    )
    return message_id


def insert_shipment(conn: sqlite3.Connection, manifest: Manifest, message_id: int) -> int:
    """Raises sqlite3.IntegrityError when the shipment was already announced."""
    cur = conn.execute(
        """INSERT INTO shipment (partner_id, shipment_ref, terminal_code, expected_arrival,
                                 message_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            manifest.partner_id,
            manifest.shipment_ref,
            manifest.terminal_code,
            manifest.expected_arrival,
            message_id,
            now(),
        ),
    )
    shipment_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO vehicle (shipment_id, vin, make, model) VALUES (?, ?, ?, ?)",
        [(shipment_id, v.vin, v.make, v.model) for v in manifest.vehicles],
    )
    return shipment_id


def register_arrival(conn: sqlite3.Connection, vin: str, event_time: str, source: str) -> sqlite3.Row | None:
    vehicle = conn.execute(
        """SELECT v.vehicle_id, v.vin, s.shipment_ref, s.partner_id
             FROM vehicle v JOIN shipment s ON s.shipment_id = v.shipment_id
            WHERE v.vin = ? AND v.status = 'EXPECTED'
            ORDER BY s.expected_arrival LIMIT 1""",
        (vin,),
    ).fetchone()
    if vehicle is None:
        return None
    conn.execute(
        "UPDATE vehicle SET status = 'ARRIVED', arrived_at = ? WHERE vehicle_id = ?",
        (event_time, vehicle["vehicle_id"]),
    )
    conn.execute(
        """INSERT INTO terminal_event (vehicle_id, vin, event_type, event_time, source)
           VALUES (?, ?, 'ARRIVED', ?, ?)""",
        (vehicle["vehicle_id"], vin, event_time, source),
    )
    return vehicle


def list_messages(conn: sqlite3.Connection, status: str | None, partner: str | None, limit: int) -> list[dict]:
    sql = """SELECT m.message_id, m.partner_code, m.message_ref, m.channel, m.status,
                    m.shipment_ref, m.vehicle_count, m.received_at, m.processed_at,
                    (SELECT GROUP_CONCAT(error_code, ', ') FROM message_error e
                      WHERE e.message_id = m.message_id) AS error_codes
               FROM edi_message m WHERE 1 = 1"""
    params: list = []
    if status:
        sql += " AND m.status = ?"
        params.append(status)
    if partner:
        sql += " AND m.partner_code = ?"
        params.append(partner)
    sql += " ORDER BY m.message_id DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(sql, params)]


def get_message(conn: sqlite3.Connection, message_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM edi_message WHERE message_id = ?", (message_id,)).fetchone()
    if row is None:
        return None
    message = dict(row)
    message["errors"] = [
        dict(r)
        for r in conn.execute(
            "SELECT error_code, field_path, detail FROM message_error WHERE message_id = ? ORDER BY error_id",
            (message_id,),
        )
    ]
    return message


def list_shipments(conn: sqlite3.Connection, limit: int) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            """SELECT s.shipment_id, s.partner_id, s.shipment_ref, s.expected_arrival,
                      COUNT(v.vehicle_id) AS vehicles,
                      SUM(CASE WHEN v.status = 'ARRIVED' THEN 1 ELSE 0 END) AS arrived
                 FROM shipment s LEFT JOIN vehicle v ON v.shipment_id = s.shipment_id
                GROUP BY s.shipment_id
                ORDER BY s.expected_arrival LIMIT ?""",
            (limit,),
        )
    ]
