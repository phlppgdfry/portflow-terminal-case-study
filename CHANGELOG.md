# Changelog

## Portfolio implementation · 22 October 2026

- Added a standalone terminal-event contract and executable gate → yard → hold → release → departure fixture.
- Added 14 acceptance tests covering ordering, source/visit boundaries, replay, conflicts and hold policy; the complete service suite has 52 tests.
- Documented reconciliation ownership and the boundary between the in-memory event reference and the existing announcement API.
- Linked reproducible output and added the scenario to CI.

This section describes actual repository work. The versions and dates below belong to the fictional case timeline.

## 1.3.0 · planned 2026-11-03 · [CR-001](changes/CR-001-new-logistics-partner.md)

- EDI: DTM format 303 (time with UTC offset), converted to terminal local time.
- Partner Gannet Auto Carriers (GNT) registered as `ONBOARDING`; activated at go-live.
- Mapping specification 1.3.

## 1.2.1 · 2026-10-01 · [CR-002](changes/CR-002-connection-leak-fix.md) (emergency)

- Fix: database connections are returned to the pool on every error path (PRB-001).
- Regression test AT-12; `/health` reports `NO_CONNECTION` separately from `DOWN`.
- Default pool size 10.

## 1.2.0 · 2026-09-24

- KPI endpoint `/api/v1/reports/kpis` and KPI tiles on the operations page.
- Datasource pool reduced from 20 to 5 at the DBA's request (see INC-001).

## 1.1.0 · 2026-08-24

- EDI channel: VMANIF parser with envelope, segment count and release character handling.
- Operations page `/ops` with rejected messages and message detail.
- Partner Heron Shipping Lines (HRN) live.

## 1.0.0 · 2026-07-20

- REST channel `/api/v1/vehicle-manifests`, validation rules BR-01 to BR-11, duplicate detection.
- Spool for messages received while the database is unavailable.
- Gate arrival registration.
- Partner Osprey Vehicle Logistics (OSP) live.
