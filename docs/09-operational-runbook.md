# 09 · Operational runbook: PortFlow

For second-line support (application management). First line (service desk) takes the call,
checks `/health`, and escalates here.

## Service at a glance

| | |
|---|---|
| What it does | Validates inbound vehicle manifests from partners; shows rejected ones to operations |
| Business impact when down | New announcements wait (not lost); planners see no new shipments; gate exceptions rise after ~2 hours |
| Operating hours | 24/7 inbound, staffed support 06:00 to 22:00 |
| Health | `GET /health` → `UP` / `DEGRADED` / `DOWN` |
| Operations page | `/ops` |
| Logs | Application server log, filter on `portflow`; one event per line (`MESSAGE_RECEIVED`, `DATABASE_TIMEOUT`, …) |
| Database | Oracle schema `PORTFLOW`; read-only account for support queries |
| Depends on | Oracle, integration layer (EDI), API gateway (REST) |
| Owner | IT Development Officer (application), IT operations (platform), DBA (database) |

## Monitoring and alerts

| Alert | Condition | Severity | First action |
|---|---|---|---|
| Service down | `/health` HTTP 503 or no answer for 2 minutes | P1 during operating hours | [R1](#r1-messages-are-not-being-processed) |
| Backlog | `pendingBacklog` > 0 for 5 minutes | P2 | [R1](#r1-messages-are-not-being-processed) |
| Pool pressure | `pool.available` < 2 of 10 for 5 minutes | P2 | [R1](#r1-messages-are-not-being-processed), step 5 |
| Rejection spike | One partner > 50 % rejected over the last hour, at least 5 messages | P3 | [R2](#r2-a-partner-gets-many-rejections) |
| Silent partner | Active partner without messages for 6 hours on a working day | P3 | [R2](#r2-a-partner-gets-many-rejections), diagnostic query Q5 |
| Slow processing | Average processing > 2 s over 15 minutes | P3 | [R3](#r3-processing-is-slow) |

The pool and backlog alerts were added after [INC-001](../incidents/INC-001-edi-processing-failure.md);
the rejection-spike alert after [INC-002](../incidents/INC-002-partner-date-format-change.md).

## R1 Messages are not being processed

Symptoms: a partner reports missing vehicles; planners see no new shipments; backlog alert.

Work from the outside in and write down the time of every finding.

1. **Is the partner connected?** Integration layer console: are interchanges from this partner
   arriving? Gateway: are REST calls arriving, and with which status code? If nothing arrives,
   it is a partner or network problem: contact the partner, check the firewall change calendar.
2. **Is it one partner or all?** Diagnostic query Q1 and Q5 ([diagnostic-queries.sql](../database/diagnostic-queries.sql)).
   One partner → probably R2. All partners → continue.
3. **Is PortFlow running?** `GET /health`. No answer → check the application server
   (`jboss-cli.sh --connect --command="deployment-info"`), the host (`topas`, `df -g`, `errpt` on AIX).
4. **Is the backlog growing?** `pendingBacklog` in `/health`. Growing means PortFlow receives but
   cannot store. Messages are safe in the spool; there is no need to ask partners to resend.
5. **Are database connections available?** `/health` → `database`:
   - `NO_CONNECTION` with `pool.available = 0`: the pool is empty. Check whether the database
     itself is fine (`sqlplus` with the support account, `SELECT 1 FROM dual`). If yes, the
     application holds the connections: ask the DBA for [dba-session-checks.sql](../database/dba-session-checks.sql)
     D1/D2. Many `INACTIVE` sessions holding transactions = leaked connections (INC-001 pattern).
   - `DOWN`: the database rejects queries. Escalate to the DBA immediately.
6. **What changed?** Check the change calendar and the last deployment (`CHANGELOG.md`,
   `deployment-info`). INC-001 started five days after a configuration change.
7. **Read the log** around the first failure: the sequence `MESSAGE_RECEIVED`,
   `VALIDATION_SUCCESS`, `DATABASE_TIMEOUT`, `RETRY_1`…`MESSAGE_PENDING` means validation works and
   storage does not.

**Recovery.**

- Pool exhausted by the application: restart the deployment
  (`jboss-cli.sh --connect --command="deployment redeploy portflow.war"`) or flush the pool
  (`/subsystem=datasources/data-source=PortFlowDS:flush-all-connection-in-pool`). The spool drains
  automatically within `PORTFLOW_SPOOL_INTERVAL`; watch `MESSAGE_RECOVERED` in the log and the
  backlog going to 0.
- Database down: DBA restores the database; PortFlow needs no restart, the spool drains.
- Afterwards: run the smoke test; tell operations which shipments arrived late in the plan;
  open a problem record if the cause is not understood ([problem analysis](../incidents/problem-analysis.md)).

## R2 A partner gets many rejections

1. Q2 in [diagnostic-queries.sql](../database/diagnostic-queries.sql): which codes, since when?
2. Open two rejected messages in `/ops` and compare the raw payload with an accepted one from last week.
3. **Same code on every message since a given moment** = a change on the partner side (INC-002).
   Call the partner's IT contact, not their operations. Ask what changed and when.
4. **Mixed codes on some messages** = data quality. Customer service handles it with the partner's
   operations team; share the codes and the [error scenarios](../integrations/error-scenarios.md).
5. Never "fix" a partner message in the database. The partner sends a corrected message with a new
   reference.

## R3 Processing is slow

1. Q6 (slow messages): one partner with huge manifests, or everything?
2. `/health` pool: few free connections means waiting on the database → DBA (top SQL, locks).
3. Host CPU/memory (`topas` / `vmstat` on AIX) and application server thread pool.
4. Recent data growth: check that `IX_MESSAGE_STATUS_RECEIVED` is used (DBA, execution plan).

## R4 Activate or suspend a partner

Activation is part of a release or a standard change, never ad hoc. Suspension may be done
immediately on request of the operations manager (for example a partner sending wrong data at volume).

```sql
UPDATE partner SET status = 'SUSPENDED' WHERE partner_id = :partner_id;
COMMIT;
```

Demo: `python -m portflow set-partner-status GNT SUSPENDED`. Effect: new messages are rejected
with `V-PARTNER-INACTIVE`; nothing already accepted changes. Record it in the RAID log.

## R5 Replay the spool by hand

Normally not needed. If the worker is stuck (backlog not decreasing while the database is fine):
restart the service; the worker starts with it and processes the spool oldest first. Never delete
spool files: each one is a partner message nobody else has.

## Escalation

| Situation | Escalate to | When |
|---|---|---|
| Database errors, sessions, performance | DBA on duty | Immediately for P1, within 30 minutes for P2 |
| Host, disk, application server | IT operations (Unix / middleware) | Immediately for P1 |
| EDI not arriving, routing | Integration team | After step 1 confirms |
| Partner-side change or outage | Partner IT contact (partner register) | After R2 step 3 |
| P1 longer than 30 minutes | IT manager; inform the operations manager | Every 30 minutes an update |

## Contacts

Kept in the partner register and the on-call schedule, not in this file (they change too often).
Roles: IT Development Officer (application owner), DBA on duty, Unix/middleware on duty,
integration team, operations shift lead, partner IT contacts.

## Known issues

| ID | Issue | Workaround | Planned fix |
|---|---|---|---|
| KI-01 | Replacement messages (BGM 5) are rejected | Partner sends a new shipment reference; customer service cancels the old one in the TOS | Backlog, [D-008](../project-management/decision-log.md) |
| KI-02 | Smoke-test shipments remain visible until cleaned up | Run the cleanup script after the smoke test | 1.4.0 |
