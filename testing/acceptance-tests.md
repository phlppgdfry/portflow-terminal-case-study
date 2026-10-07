# Acceptance tests

Acceptance criteria for the functional requirements, written as testable scenarios. Most are
automated; the automated test name is given so anyone can see exactly what is checked
(`service/tests/`). UAT repeats the Must cases by hand on ACC through the API and the operations page.

| ID | Requirement | Given | When | Then | Automated |
|---|---|---|---|---|---|
| AT-01 | FR-001 | Active REST partner OSP | It posts a valid manifest with 3 vehicles | HTTP 201 `ACCEPTED`; 1 shipment, 3 vehicles `EXPECTED`; arrival in local time | `test_at01_valid_rest_manifest_is_accepted` |
| AT-02 | FR-002 | Active EDI partner HRN | The sample VMANIF arrives | `ACCEPTED`; 4 vehicles stored | `test_at02_valid_edi_manifest_is_accepted` |
| AT-03 | FR-003, FR-004 | A manifest with a VIN containing O and a vehicle without VIN | It is submitted | `REJECTED` with `V-VIN-FORMAT` and `V-REQUIRED`; errors stored; **no** shipment created | `test_at03_invalid_vehicle_data_is_rejected_and_explained` |
| AT-04 | FR-004 | Partner code XYZ is not registered | It submits a manifest | `REJECTED`, `V-PARTNER-UNKNOWN` | `test_at04_unknown_partner_is_rejected` |
| AT-05 | FR-006 | A manifest was accepted | The same message is sent again | HTTP 200 `DUPLICATE` with the original id; still one message row | `test_at05_duplicate_message_is_ignored` |
| AT-06 | FR-007 | Shipment OSP-2026-03317 was accepted | It is sent again under a new message reference | `REJECTED`, `V-SHIPMENT-EXISTS`; vehicle count unchanged | `test_at06_shipment_announced_twice_is_rejected` |
| AT-07 | FR-009 | No database connection is available | A valid manifest arrives | HTTP 202 `PENDING`, message in the spool; after recovery it is `ACCEPTED` and the spool is empty | `test_at07_database_unavailable_message_waits_and_recovers` |
| AT-08 | FR-010 | — | A truncated EDI interchange arrives | `REJECTED`, `E-SYNTAX`; raw payload stored | `test_at08_unreadable_payload_is_stored_as_rejected` |
| AT-09 | FR-008 | GNT has status `ONBOARDING` | GNT sends a valid manifest; then GNT is activated and sends again | First `V-PARTNER-INACTIVE`, then `ACCEPTED` | `test_at09_partner_in_onboarding_is_rejected_until_activated` |
| AT-10 | FR-005 | A manifest was rejected for two reasons | An operations user filters on Rejected and opens it | The message is listed; the detail shows both codes and the raw payload | `test_at10_operations_can_see_why_a_message_was_rejected` |
| AT-11 | FR-011 | A vehicle is expected | The gate posts an arrival for its VIN | HTTP 201; shipment shows 1 of 3 arrived | `test_at11_gate_arrival_updates_the_shipment` |
| AT-12 | NFR-09, PRB-001 | Pool of 3 connections | Ten units of work fail in a row | All 3 connections are available afterwards | `test_at12_prb001_pool_is_whole_after_failed_units_of_work` |
| AT-13 | FR-012 | Messages exist | KPIs are requested | Per-status counts, partners, top errors, arrivals, processing time returned | `test_at13_kpis_are_available` |
| AT-14 | FR-008 | HRN is set up for EDI | HRN posts over REST | `REJECTED`, `V-PARTNER-CHANNEL` | `test_at14_partner_must_use_its_registered_channel` |
| AT-15 | FR-013 | Gannet sends 11:30 UTC (format 303) in October | The manifest is mapped | Arrival stored as 13:30 local; in December 12:30 | `test_at15_utc_arrival_is_converted_to_terminal_time`, `test_winter_time_offset` |

## UAT script (by hand, on ACC)

For each Must case above, the tester:

1. Sends the prepared file (Postman collection or the integration layer's test sender).
2. Checks the HTTP answer or the EDI notice.
3. Opens `/ops` and checks the message status and, for rejections, the reasons.
4. For accepted manifests: checks the shipment in the expected-shipments list.
5. Records pass / fail with a screenshot in the UAT log.

Sign-off by the operations manager when all Must cases pass and no severity 1 or 2 defect is open.
