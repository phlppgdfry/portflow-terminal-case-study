"""EDI channel: an EDIFACT-style vehicle manifest (message type VMANIF).

VMANIF is a fictional message defined for this case study. It uses real
UN/EDIFACT syntax (UNA/UNB/UNH envelope, ' + : separators, ? release
character, UNT segment count) so the parser has to deal with the same things
a real EDI integration does. The message implementation guide is in
integrations/mapping-specification.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from .mapping import PayloadSyntaxError, parse_edi_arrival
from .model import Issue, Manifest, Vehicle

DEFAULT_SEPARATORS = ":+.? '"  # component, element, decimal, release, reserved, segment


@dataclass
class Segment:
    tag: str
    elements: list[list[str]]

    def value(self, element: int, component: int = 0) -> str:
        try:
            return self.elements[element][component].strip()
        except IndexError:
            return ""


def tokenize(text: str) -> list[Segment]:
    text = text.strip()
    separators = DEFAULT_SEPARATORS
    if text.startswith("UNA"):
        separators, text = text[3:9], text[9:]
        if len(separators) != 6:
            raise PayloadSyntaxError("UNA service string advice is incomplete")
    comp, elem, _decimal, release, _reserved, term = separators

    segments: list[Segment] = []
    elements: list[list[str]] = []
    components: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == release and i + 1 < len(text):
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == comp:
            components.append("".join(buf))
            buf = []
        elif ch == elem:
            components.append("".join(buf))
            elements.append(components)
            components, buf = [], []
        elif ch == term:
            components.append("".join(buf))
            elements.append(components)
            tag = elements[0][0].strip()
            if not tag:
                raise PayloadSyntaxError(f"empty segment tag after segment {len(segments)}")
            segments.append(Segment(tag, elements[1:]))
            elements, components, buf = [], [], []
        elif ch not in "\r\n":
            buf.append(ch)
        i += 1
    if "".join(buf).strip() or elements or components:
        raise PayloadSyntaxError("message does not end with a segment terminator")
    return segments


def from_edi(raw: str) -> tuple[Manifest, list[Issue]]:
    segments = tokenize(raw)
    if not segments or segments[0].tag != "UNB":
        raise PayloadSyntaxError("interchange must start with UNB")
    if segments[-1].tag != "UNZ":
        raise PayloadSyntaxError("interchange must end with UNZ")

    unb, unz = segments[0], segments[-1]
    control_ref = unb.value(4)
    if unz.value(1) != control_ref:
        raise PayloadSyntaxError(
            f"UNZ control reference '{unz.value(1)}' does not match UNB '{control_ref}'"
        )

    body = segments[1:-1]
    if not body or body[0].tag != "UNH" or body[-1].tag != "UNT":
        raise PayloadSyntaxError("interchange must contain exactly one UNH...UNT message")
    unh, unt = body[0], body[-1]
    if unh.value(1, 0) != "VMANIF":
        raise PayloadSyntaxError(f"unsupported message type '{unh.value(1, 0)}'")
    if unt.value(0) != str(len(body)):
        raise PayloadSyntaxError(
            f"UNT segment count is {unt.value(0) or '(empty)'} but the message has {len(body)}"
        )
    if unt.value(1) != unh.value(0):
        raise PayloadSyntaxError("UNT message reference does not match UNH")

    manifest = Manifest(channel="EDI", partner_id=unb.value(1) or None, message_ref=control_ref or None)
    issues: list[Issue] = []
    current: Vehicle | None = None

    for seg in body[1:-1]:
        if seg.tag == "BGM":
            manifest.shipment_ref = seg.value(1) or None
            function = seg.value(2)
            if function and function != "9":
                issues.append(
                    Issue("V-FUNCTION", "BGM", f"message function {function} not supported; only 9 (original)")
                )
        elif seg.tag == "DTM" and seg.value(0, 0) == "132":
            manifest.expected_arrival, issue = parse_edi_arrival(seg.value(0, 1), seg.value(0, 2))
            if issue:
                issues.append(issue)
        elif seg.tag == "LOC" and seg.value(0) == "11":
            manifest.terminal_code = seg.value(1) or None
        elif seg.tag == "GID":
            current = Vehicle(vin=None)
            manifest.vehicles.append(current)
        elif seg.tag == "PIA" and current is not None and seg.value(1, 1) == "VIN":
            current.vin = seg.value(1, 0) or None
        elif seg.tag == "IMD" and current is not None:
            current.make = seg.value(2, 3) or None
            current.model = seg.value(2, 4) or None
        # Other segments are ignored (tolerant reader); see the mapping spec.

    return manifest, issues
