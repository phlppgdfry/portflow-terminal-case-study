"""Business rules that need no database (BR-01..BR-06 in docs/02-business-requirements.md).

Partner rules (BR-07, BR-08) and shipment uniqueness (BR-09) need reference
data and are checked inside the database unit of work in service.py.
"""

from __future__ import annotations

import re

from .model import Issue, Manifest

# 17 characters, digits and capitals, never I, O or Q (ISO 3779).
# The check digit in position 9 is only mandatory for North American VINs,
# so it is not enforced: European manufacturers often put a letter there.
VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
MAX_VEHICLES = 1000


def validate(manifest: Manifest, terminal_code: str, mapping_issues: list[Issue] = ()) -> list[Issue]:
    """Return the rule violations; `mapping_issues` avoids reporting a bad date twice."""
    issues: list[Issue] = []

    for field, value in (
        ("partnerId", manifest.partner_id),
        ("messageRef", manifest.message_ref),
        ("shipmentId", manifest.shipment_ref),
        ("terminalCode", manifest.terminal_code),
    ):
        if not value:
            issues.append(Issue("V-REQUIRED", field, f"{field} is mandatory"))

    if manifest.expected_arrival is None and not any(
        i.code == "V-ARRIVAL-DATE" for i in mapping_issues
    ):
        issues.append(Issue("V-REQUIRED", "expectedArrival", "expectedArrival is mandatory"))

    if manifest.terminal_code and manifest.terminal_code != terminal_code:
        issues.append(
            Issue("V-TERMINAL", "terminalCode", f"'{manifest.terminal_code}' is not this terminal ({terminal_code})")
        )

    if not manifest.vehicles:
        issues.append(Issue("V-NO-VEHICLES", "vehicles", "the manifest contains no vehicles"))
    elif len(manifest.vehicles) > MAX_VEHICLES:
        issues.append(Issue("V-TOO-MANY", "vehicles", f"more than {MAX_VEHICLES} vehicles in one manifest"))

    seen: set[str] = set()
    for index, vehicle in enumerate(manifest.vehicles):
        path = f"vehicles[{index}].vin"
        if not vehicle.vin:
            issues.append(Issue("V-REQUIRED", path, "VIN is mandatory"))
        elif not VIN_PATTERN.match(vehicle.vin):
            issues.append(Issue("V-VIN-FORMAT", path, f"'{vehicle.vin}' is not a valid VIN"))
        elif vehicle.vin in seen:
            issues.append(Issue("V-VIN-DUPLICATE", path, f"VIN {vehicle.vin} appears more than once"))
        else:
            seen.add(vehicle.vin)

    return issues
