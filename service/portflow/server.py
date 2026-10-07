"""HTTP API and operations page (standard library only).

Routes are specified in integrations/openapi.yaml.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from urllib.parse import parse_qs, urlparse

from . import __version__, db, reports
from .config import Settings
from .service import ManifestService, Spool

log = logging.getLogger("portflow")
MAX_BODY = 1_000_000
UNAVAILABLE = object()  # returned by Handler._read after it already answered 503


class App:
    def __init__(self, settings: Settings):
        db.init_schema(settings.db_path)
        self.settings = settings
        self.pool = db.ConnectionPool(
            settings.db_path, settings.pool_size, settings.pool_timeout, settings.fault_leak_on_error
        )
        self.spool = Spool(settings.spool_dir)
        self.service = ManifestService(settings, self.pool, self.spool)

    def health(self) -> tuple[int, dict]:
        # NO_CONNECTION = the pool is empty (the database itself may be fine,
        # check it directly); DOWN = a connection was available but the query failed.
        database = "UP"
        try:
            with self.pool.connection(timeout=0.5) as conn:
                conn.execute("SELECT 1").fetchone()
        except db.PoolTimeout:
            database = "NO_CONNECTION"
        except Exception:  # noqa: BLE001 - any other failure means the database is not usable
            database = "DOWN"
        backlog = len(self.spool)
        if database != "UP":
            status = "DOWN"
        elif backlog or self.pool.available == 0:
            status = "DEGRADED"
        else:
            status = "UP"
        body = {
            "status": status,
            "version": __version__,
            "database": database,
            "pool": {"size": self.pool.size, "available": self.pool.available},
            "pendingBacklog": backlog,
        }
        return (503 if status == "DOWN" else 200), body


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = f"PortFlow/{__version__}"

        def log_message(self, fmt: str, *args) -> None:
            log.debug("HTTP %s", fmt % args)

        # -- helpers --------------------------------------------------------

        def _send(self, status: int, body: object, content_type: str = "application/json") -> None:
            data = body if isinstance(body, bytes) else json.dumps(body, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> str | None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self._send(413, {"error": f"payload larger than {MAX_BODY} bytes"})
                return None
            return self.rfile.read(length).decode("utf-8", errors="replace")

        def _read(self, fn):
            try:
                with app.pool.connection() as conn:
                    return fn(conn)
            except db.PoolTimeout:
                self._send(503, {"error": "database unavailable"})
                return UNAVAILABLE

        # -- routes ---------------------------------------------------------

        def do_GET(self) -> None:  # noqa: N802
            url = urlparse(self.path)
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            path = url.path.rstrip("/") or "/"

            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/ops")
                self.end_headers()
            elif path == "/ops":
                page = resources.files("portflow").joinpath("static/ops.html").read_bytes()
                self._send(200, page, "text/html; charset=utf-8")
            elif path == "/health":
                self._send(*app.health())
            elif path == "/api/v1/messages":
                limit = min(int(query.get("limit", 50)), 500)
                rows = self._read(lambda c: db.list_messages(c, query.get("status"), query.get("partner"), limit))
                if rows is not UNAVAILABLE:
                    self._send(200, rows)
            elif match := re.fullmatch(r"/api/v1/messages/(\d+)", path):
                message = self._read(lambda c: db.get_message(c, int(match.group(1))))
                if message is None:
                    self._send(404, {"error": "message not found"})
                elif message is not UNAVAILABLE:
                    self._send(200, message)
            elif path == "/api/v1/shipments":
                rows = self._read(lambda c: db.list_shipments(c, min(int(query.get("limit", 50)), 500)))
                if rows is not UNAVAILABLE:
                    self._send(200, rows)
            elif path == "/api/v1/reports/kpis":
                data = self._read(reports.kpis)
                if data is not UNAVAILABLE:
                    data["pendingBacklog"] = len(app.spool)
                    self._send(200, data)
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path.rstrip("/")
            if path in ("/api/v1/vehicle-manifests", "/api/v1/edi-messages"):
                body = self._body()
                if body is None:
                    return
                channel = "REST" if path.endswith("vehicle-manifests") else "EDI"
                outcome = app.service.submit(body, channel)
                status = outcome.http_status
                if any(e.code == "E-SYNTAX" for e in outcome.errors):
                    status = 400
                self._send(status, outcome.as_dict())
            elif path == "/api/v1/gate-events":
                self._gate_event()
            else:
                self._send(404, {"error": "not found"})

        def _gate_event(self) -> None:
            body = self._body()
            if body is None:
                return
            try:
                event = json.loads(body)
                vin, event_type = event["vin"], event.get("eventType", "ARRIVED")
            except (json.JSONDecodeError, KeyError, TypeError):
                self._send(400, {"error": "expected {\"vin\": ..., \"eventType\": \"ARRIVED\"}"})
                return
            if event_type != "ARRIVED":
                self._send(422, {"error": f"event type {event_type} not supported"})
                return
            vehicle = self._read(
                lambda c: db.register_arrival(c, vin, event.get("eventTime") or db.now(), event.get("source", "GATE"))
            )
            if vehicle is UNAVAILABLE:
                return
            if vehicle is None:
                self._send(404, {"error": f"no expected vehicle with VIN {vin}"})
                return
            log.info("VEHICLE_ARRIVED vin=%s shipment=%s", vin, vehicle["shipment_ref"])
            self._send(201, {"vin": vin, "shipment": vehicle["shipment_ref"], "status": "ARRIVED"})

    return Handler


def start_spool_worker(app: App, stop: threading.Event) -> threading.Thread:
    def run() -> None:
        while not stop.wait(app.settings.spool_interval):
            if len(app.spool):
                app.service.drain_spool()

    thread = threading.Thread(target=run, name="spool-worker", daemon=True)
    thread.start()
    return thread


def serve(settings: Settings, host: str, port: int) -> None:
    app = App(settings)
    stop = threading.Event()
    start_spool_worker(app, stop)
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    log.info(
        "SERVICE_STARTED version=%s port=%d pool_size=%d db=%s",
        __version__, port, settings.pool_size, settings.db_path,
    )
    if settings.fault_leak_on_error:
        log.warning("FAULT_INJECTION leak_on_error=on (reproduces INC-001, never use in production)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        httpd.server_close()
        app.pool.close()
        log.info("SERVICE_STOPPED")
