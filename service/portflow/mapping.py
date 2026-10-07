"""Partner format -> canonical model, for the REST/JSON channel.

Also holds the date handling shared with the EDI mapping: the terminal plans
in local time, so every arrival time is normalised to Europe/Brussels.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .model import Issue, Manifest, Vehicle

TERMINAL_TZ = ZoneInfo("Europe/Brussels")
LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class PayloadSyntaxError(ValueError):
    """The payload cannot be read at all (invalid JSON or EDI envelope)."""


def to_terminal_time(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(TERMINAL_TZ).replace(tzinfo=None)
    return value.strftime(LOCAL_FORMAT)


def parse_iso_arrival(raw: object) -> tuple[str | None, Issue | None]:
    if raw is None or raw == "":
        return None, None  # reported as V-REQUIRED by validation
    if not isinstance(raw, str):
        return None, Issue("V-ARRIVAL-DATE", "expectedArrival", "expected an ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None, Issue("V-ARRIVAL-DATE", "expectedArrival", f"'{raw}' is not ISO 8601")
    if len(raw) <= 10:
        return None, Issue(
            "V-ARRIVAL-DATE", "expectedArrival", "a time of day is required for yard planning"
        )
    return to_terminal_time(parsed), None


_UTC_OFFSET = re.compile(r"^(\d{12})([+-])(\d{2})$")


def parse_edi_arrival(value: str, fmt: str) -> tuple[str | None, Issue | None]:
    """DTM format codes as defined in the VMANIF implementation guide.

    203 = CCYYMMDDHHMM in terminal local time
    303 = CCYYMMDDHHMM followed by a UTC offset in hours, e.g. 202610081200+00
    102 = CCYYMMDD (date only) is deliberately not accepted (see decision D-006).
    """
    try:
        if fmt == "203":
            return to_terminal_time(datetime.strptime(value, "%Y%m%d%H%M")), None
        if fmt == "303":
            match = _UTC_OFFSET.match(value)
            if not match:
                raise ValueError(value)
            stamp, sign, hours = match.groups()
            offset = timedelta(hours=int(hours)) * (1 if sign == "+" else -1)
            moment = datetime.strptime(stamp, "%Y%m%d%H%M").replace(tzinfo=timezone(offset))
            return to_terminal_time(moment), None
    except ValueError:
        return None, Issue("V-ARRIVAL-DATE", "DTM+132", f"'{value}' does not match format {fmt}")
    return None, Issue(
        "V-ARRIVAL-DATE", "DTM+132", f"date format {fmt or '(none)'} not accepted; use 203 or 303"
    )


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def from_json(raw: str) -> tuple[Manifest, list[Issue]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PayloadSyntaxError(f"invalid JSON: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(payload, dict):
        raise PayloadSyntaxError("the manifest must be a JSON object")

    arrival, issue = parse_iso_arrival(payload.get("expectedArrival"))
    vehicles_raw = payload.get("vehicles")
    vehicles = []
    if isinstance(vehicles_raw, list):
        for item in vehicles_raw:
            item = item if isinstance(item, dict) else {}
            vehicles.append(
                Vehicle(
                    vin=_text(item.get("vin")),
                    make=_text(item.get("make")),
                    model=_text(item.get("model")),
                )
            )
    manifest = Manifest(
        channel="REST",
        partner_id=_text(payload.get("partnerId")),
        message_ref=_text(payload.get("messageRef")),
        shipment_ref=_text(payload.get("shipmentId")),
        expected_arrival=arrival,
        terminal_code=_text(payload.get("terminalCode")),
        vehicles=vehicles,
    )
    return manifest, [issue] if issue else []
