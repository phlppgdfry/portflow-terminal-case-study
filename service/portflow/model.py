"""Canonical data model.

Both inbound channels (REST/JSON and EDI) are mapped onto these classes, so
validation and persistence never need to know which format a partner used.
See integrations/mapping-specification.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Vehicle:
    vin: str | None
    make: str | None = None
    model: str | None = None


@dataclass
class Manifest:
    channel: str  # "REST" or "EDI"
    partner_id: str | None = None
    message_ref: str | None = None
    shipment_ref: str | None = None
    # Terminal local time (Europe/Brussels), "YYYY-MM-DDTHH:MM".
    expected_arrival: str | None = None
    terminal_code: str | None = None
    vehicles: list[Vehicle] = field(default_factory=list)


@dataclass(frozen=True)
class Issue:
    """A business rule violation. Codes are listed in integrations/error-scenarios.md."""

    code: str
    field: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "field": self.field, "message": self.message}
