# 04 · Technical specification

The technical specification (*technisch lastenboek*) for PortFlow release 1.3.0. It is what a
developer, a vendor or an integration team needs to build, test and run the component. It
traces back to the requirements in [02](02-business-requirements.md).

| | |
|---|---|
| Document owner | IT Development Officer |
| Status | Approved for release 1.3.0 (CAB 2026-10-06) |
| Implements | FR-001 to FR-013, NFR-01 to NFR-09 |
| Reference implementation | [`service/`](../service/) |

## 1. Purpose and boundaries

PortFlow receives vehicle manifests, validates them, stores the outcome and makes it visible. It
does **not** plan the yard, and it does not talk to partners directly: authentication and
transport sit in the gateway / integration layer in front of it.

## 2. Interfaces

| ID | Interface | Direction | Protocol | Format | Spec |
|---|---|---|---|---|---|
| IF-01 | Vehicle manifest (REST) | Partner → gateway → PortFlow | HTTPS, synchronous | JSON | [openapi.yaml](../integrations/openapi.yaml) |
| IF-02 | Vehicle manifest (EDI) | Partner → integration layer → PortFlow | AS2 or SFTP to the integration layer, HTTP to PortFlow | VMANIF (EDIFACT syntax) | [mapping specification](../integrations/mapping-specification.md) |
| IF-03 | Gate arrival | Gate application → PortFlow | HTTP | JSON | [openapi.yaml](../integrations/openapi.yaml) |
| IF-04 | Pre-advice to TOS | PortFlow → TOS | to be agreed with the TOS vendor | — | Phase 3, not in this release |
| IF-05 | Reporting | BI tool → Oracle | SQL (read-only views) | — | [11 · Reporting](11-reporting-and-kpis.md) |

## 3. Data

Logical model and table definitions: [data model](../database/data-model.md) and
[schema.sql](../database/schema.sql). Key decisions:

- One table `EDI_MESSAGE` for both channels, with the raw payload, so support has one place to look.
- Idempotency key `(partner_code, message_ref)`, a function-based unique index in Oracle.
- `UQ_SHIPMENT_PARTNER_REF` enforces BR-09 in the database, not only in code.
- Times are stored as terminal local time (`TIMESTAMP`), see FR-013.

## 4. Processing logic

For each inbound message (implemented in [`service.py`](../service/portflow/service.py)):

1. Log `MESSAGE_RECEIVED`.
2. Parse with the channel parser. A syntax error becomes the single issue `E-SYNTAX`.
3. Map to the canonical manifest ([`model.py`](../service/portflow/model.py)).
4. Run content rules BR-01 to BR-06 ([`validation.py`](../service/portflow/validation.py)).
   Log `VALIDATION_SUCCESS` or `VALIDATION_FAILED`.
5. Open one database unit of work (one connection, one transaction):
   1. duplicate check → `DUPLICATE`, commit nothing;
   2. partner rules BR-07, BR-08;
   3. with issues: insert message as `REJECTED` and its errors;
   4. without issues: insert message `ACCEPTED`, shipment, vehicles.
6. If the shipment insert violates `UQ_SHIPMENT_PARTNER_REF`: roll back, then store the message
   as `REJECTED` with `V-SHIPMENT-EXISTS` in a new unit of work.
7. If no connection is available or the database errors: retry with linear back-off; after the
   last attempt write the message to the **spool** and answer `PENDING`.
8. A background worker retries the spool every `PORTFLOW_SPOOL_INTERVAL` seconds, oldest first,
   and stops at the first failure so the order is kept.

**Connection handling rule** (from [PRB-001](../incidents/problem-analysis.md)): every borrowed
connection is returned to the pool in a `finally` block, on the success path and on every error
path. A regression test (`test_at12_prb001_pool_is_whole_after_failed_units_of_work`) guards it.

## 5. Configuration

| Parameter | Default | Meaning |
|---|---|---|
| `PORTFLOW_DB` | `portflow.db` | Database location (target: JNDI datasource `java:/jdbc/PortFlowDS`) |
| `PORTFLOW_POOL_SIZE` | 10 | Maximum connections; NFR-09 caps this at 10 |
| `PORTFLOW_POOL_TIMEOUT` | 2.0 s | Wait for a free connection before `DATABASE_TIMEOUT` |
| `PORTFLOW_DB_RETRIES` | 3 | Retries after the first attempt |
| `PORTFLOW_RETRY_BACKOFF` | 0.5 s | Back-off step (0.5, 1.0, 1.5 s) |
| `PORTFLOW_SPOOL_DIR` | `spool` | Durable directory for pending messages; must survive a restart |
| `PORTFLOW_SPOOL_INTERVAL` | 5 s | Spool retry interval |
| `PORTFLOW_TERMINAL_CODE` | `BEZEE` | Terminal this instance accepts (BR-04) |
| `PORTFLOW_FAULT_LEAK_ON_ERROR` | off | Demo only: re-introduces the 1.2.0 leak to replay INC-001 |

On JBoss EAP the pool settings map to the datasource: `max-pool-size`, `blocking-timeout-wait-millis`,
and `background-validation` for broken connections ([10 · Infrastructure](10-infrastructure-and-application-server.md)).

## 6. Logging and monitoring

One line per event, key=value, so log tooling can parse it without a custom grammar.

| Event | Level | When |
|---|---|---|
| `MESSAGE_RECEIVED` | INFO | Every inbound message |
| `VALIDATION_SUCCESS` / `VALIDATION_FAILED` | INFO / WARN | After content rules, with the codes |
| `MESSAGE_ACCEPTED` / `MESSAGE_REJECTED` / `MESSAGE_DUPLICATE` | INFO / WARN / INFO | Outcome |
| `SHIPMENT_CONFLICT` | WARN | BR-09 violation from the database |
| `DATABASE_TIMEOUT` | ERROR | No connection or database error, per attempt |
| `RETRY_n` | WARN | Before retry n |
| `MESSAGE_PENDING` | ERROR | Message moved to the spool, with backlog size |
| `MESSAGE_RECOVERED` | INFO | Spooled message processed |
| `VEHICLE_ARRIVED` | INFO | Gate event |

Health endpoint `GET /health`: `UP`, `DEGRADED` (backlog > 0 or no free connection) or `DOWN`
(HTTP 503). Database state `UP`, `NO_CONNECTION` (pool empty; the database itself may be fine) or
`DOWN`. Alert rules are in the [runbook](09-operational-runbook.md#monitoring-and-alerts).

## 7. Security

- Partner authentication and TLS end at the gateway; PortFlow trusts only the gateway network.
- The partner id in the message must belong to the authenticated partner (gateway check; listed
  in the [CR-001 impact analysis](../changes/impact-analysis.md)).
- Database: application account with DML on its own tables; a separate read-only account for
  reporting and support queries; DDL only through releases.
- Raw payloads contain VINs and shipment references, no personal data. Retention 90 days.
- Request size limit 1 MB (413 above).

## 8. Error handling summary

Full list with partner actions: [error scenarios](../integrations/error-scenarios.md).

| Situation | HTTP | Stored | Recovery |
|---|---|---|---|
| Business rule fails | 422 | REJECTED + errors | Partner sends a corrected message with a new reference |
| Unreadable payload | 400 | REJECTED + `E-SYNTAX` | Partner fixes the format |
| Duplicate | 200 | — | None needed |
| Database unavailable | 202 | Spool | Automatic |

## 9. Traceability

| Requirement | Component | Test |
|---|---|---|
| FR-001, FR-002 | `mapping.py`, `edi.py`, `server.py` | AT-01, AT-02, `test_mapping.py` |
| FR-003, FR-004 | `validation.py`, `service.py` | AT-03, AT-04, `test_validation.py` |
| FR-005 | `db.get_message`, `/ops` | AT-10 |
| FR-006, FR-007 | unique keys, `service._store` | AT-05, AT-06 |
| FR-008 | `service._partner_issues` | AT-09, AT-14 |
| FR-009 | retry, `Spool`, spool worker | AT-07 |
| FR-010 | `PayloadSyntaxError` handling | AT-08 |
| FR-011 | `db.register_arrival` | AT-11 |
| FR-012 | `reports.py`, Oracle views | AT-13 |
| FR-013 | `mapping.to_terminal_time` | AT-15 |
| NFR-09 | pool, PRB-001 fix | AT-12 |
