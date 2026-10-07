# Mapping specification

Message implementation guide (MIG) for partners, and the field mapping onto PortFlow's canonical
model. Version 1.3 (adds DTM format 303 for [CR-001](../changes/CR-001-new-logistics-partner.md)).

## REST (JSON) → canonical

| JSON field | Canonical | Database column | Rule | Notes |
|---|---|---|---|---|
| `partnerId` | `partner_id` | `EDI_MESSAGE.partner_code`, `SHIPMENT.partner_id` | BR-01, BR-07, BR-08 | Issued at onboarding |
| `messageRef` | `message_ref` | `EDI_MESSAGE.message_ref` | BR-01, BR-10 | Max 35; unique per partner |
| `shipmentId` | `shipment_ref` | `SHIPMENT.shipment_ref` | BR-01, BR-09 | Max 35 |
| `expectedArrival` | `expected_arrival` | `SHIPMENT.expected_arrival` | BR-01, BR-05 | ISO 8601 incl. time; offset converted to Europe/Brussels; no offset = local |
| `terminalCode` | `terminal_code` | `SHIPMENT.terminal_code` | BR-04 | `BEZEE` |
| `vehicles[].vin` | `vehicles[].vin` | `VEHICLE.vin` | BR-02, BR-03 | Trimmed; upper case required |
| `vehicles[].make` | `vehicles[].make` | `VEHICLE.make` | — | Optional |
| `vehicles[].model` | `vehicles[].model` | `VEHICLE.model` | — | Optional |

Unknown JSON fields are ignored, so partners can add fields without breaking the interface.

## EDI: VMANIF message

**Syntax.** UN/EDIFACT syntax version 3 (`UNOC`), default separators: component `:`, element `+`,
decimal `.`, release `?`, segment terminator `'`. `UNA` is optional. Line breaks between segments
are allowed and ignored.

**Status.** `VMANIF` is a message type defined for this case study, using EDIFACT syntax and
segment tags so the integration concerns are realistic. With a real partner this would be
agreed on a standard message.

### Segment table

| Pos | Segment | Name | Status | Repeat | Content |
|---|---|---|---|---|---|
| 0 | `UNA` | Service string advice | C | 1 | `UNA:+.? '` |
| 1 | `UNB` | Interchange header | M | 1 | Syntax `UNOC:3`, sender, recipient `PORTFLOW`, date/time, **control reference** |
| 2 | `UNH` | Message header | M | 1 | Message ref, type `VMANIF:1:0:PF` |
| 3 | `BGM` | Beginning of message | M | 1 | `VMN`, **shipment reference**, function `9` (original) |
| 4 | `DTM` | Date/time | M | 1 | Qualifier `132` (expected arrival) |
| 5 | `LOC` | Place | M | 1 | Qualifier `11`, terminal code |
| 6 | `NAD` | Party | C | 1 | `CA` carrier; informative, not used |
| 7 | `FTX` | Free text | C | 9 | Informative, not used |
| 8 | `GID` | Goods item | M | 1000 | Starts one vehicle; sequence number |
| 9 | `PIA` | Product identification | M | 1 per GID | `5` + `VIN:VIN` |
| 10 | `IMD` | Item description | C | 1 per GID | `F++:::make:model` |
| 11 | `UNT` | Message trailer | M | 1 | **Segment count** UNH..UNT, message ref |
| 12 | `UNZ` | Interchange trailer | M | 1 | Message count, control reference (= UNB) |

M = mandatory, C = conditional. Other segments are ignored (tolerant reader), so a partner can
send extra information without a rejection.

### EDI → canonical

| Partner field | Segment / element | Canonical | Example |
|---|---|---|---|
| Sender id | `UNB` 0004 (element 2, component 1) | `partner_id` | `HRN` |
| Interchange control reference | `UNB` 0020 (element 5) | `message_ref` | `000125` |
| Shipment number | `BGM` 1004 (element 2) | `shipment_ref` | `HRN-2026-00125` |
| Message function | `BGM` 1225 (element 3) | — (must be `9`) | `9` |
| Expected arrival | `DTM` C507: `132:value:format` | `expected_arrival` | `132:202610081400:203` |
| Terminal | `LOC` 3225 with qualifier `11` | `terminal_code` | `BEZEE` |
| VIN | `PIA` C212 with type `VIN` | `vehicles[].vin` | `WVWZZZE1ZPP012345:VIN` |
| Make / model | `IMD` C273 descriptions 1 and 2 | `make`, `model` | `:::Volkswagen:ID.4` |

### Date formats (DTM 2379)

| Code | Pattern | Meaning | Accepted |
|---|---|---|---|
| `203` | `CCYYMMDDHHMM` | Terminal local time | Yes |
| `303` | `CCYYMMDDHHMM±HH` | Time with UTC offset in hours, e.g. `202610091130?+00` | Yes, since 1.3 (CR-001) |
| `102` | `CCYYMMDD` | Date only | **No**: yard planning needs a time ([D-006](../project-management/decision-log.md)) |

Note the `?+` in format 303: `+` is the element separator, so a plus sign inside data must be
released with `?`. Gannet's first test file sent `+00` unreleased, which splits the element; the
parser then sees a malformed date and rejects with `V-ARRIVAL-DATE`. This is in the partner test
set ([12 · Partner onboarding](../docs/12-partner-onboarding.md)).

### Envelope checks (before any business rule)

| Check | Failure |
|---|---|
| First segment `UNB`, last `UNZ` | `E-SYNTAX` |
| `UNZ` control reference equals `UNB` control reference | `E-SYNTAX` |
| Exactly one `UNH`…`UNT` | `E-SYNTAX` |
| Message type `VMANIF` | `E-SYNTAX` |
| `UNT` segment count equals actual count | `E-SYNTAX` (typical for truncated files) |
| Last character is a segment terminator | `E-SYNTAX` |

## Samples

| File | Partner | Purpose | Expected |
|---|---|---|---|
| [sample-vehicle-import.json](sample-vehicle-import.json) | OSP | REST, 3 vehicles, offset +02:00 | ACCEPTED |
| [sample-edi-message.edi](sample-edi-message.edi) | HRN | EDI, 4 vehicles, released `?:` in FTX | ACCEPTED |
| [sample-edi-gnt-utc.edi](sample-edi-gnt-utc.edi) | GNT | Format 303, 11:30 UTC → 13:30 local | ACCEPTED once GNT is active |
| [sample-edi-invalid.edi](sample-edi-invalid.edi) | HRN | Format 102 and a VIN with the letter O | REJECTED (`V-ARRIVAL-DATE`, `V-VIN-FORMAT`) |

The automated tests read these files, so the samples in this specification are always valid
examples of what they claim.
