# INC-001 · Partner messages are no longer processed

| | |
|---|---|
| Priority | P2: major degradation, no data loss, workaround available |
| Opened / resolved | 2026-09-29 09:48 / 2026-09-29 11:05 |
| Service impact | 09:41 to 10:08 (27 minutes): no manifest stored; all messages pending |
| Reported by | Osprey Vehicle Logistics (partner), confirmed by the planning office |
| Handled by | IT Development Officer (second line), DBA, middleware on duty |
| Version | PortFlow 1.2.0 |
| Problem record | [PRB-001](problem-analysis.md#prb-001-recurring-database-connection-exhaustion) |

## Symptoms and timeline

| Time | What happened |
|---|---|
| 07:55 | Heron starts resending manifests for vessel shipments after a rotation change, under new interchange references. Each resend is rejected `V-SHIPMENT-EXISTS`, as designed. |
| 09:41 | First `DATABASE_TIMEOUT` in the log. From here every message ends `PENDING`. |
| 09:42 | Osprey's integration team calls: their manifests get HTTP 202 instead of 201, and the shipments are not in the terminal's planning. |
| 09:45 | Planning office confirms: 126 vehicles expected this afternoon are missing from the plan. |
| 09:48 | Incident opened. `/health`: `DOWN`, database `NO_CONNECTION`, pool `0/5`, backlog 9. |
| 09:52 | Backlog growing (11). Database checked directly with the support account: `SELECT 1 FROM dual` answers immediately. **The database is fine; the application holds every connection.** |
| 09:58 | DBA runs [dba-session-checks.sql](../database/dba-session-checks.sql) D1: five `INACTIVE` sessions from the application host. Their idle times match the five `SHIPMENT_CONFLICT` log lines since Sunday's weekly restart (one on Monday, four this morning). |
| 10:05 | Workaround agreed with the middleware team: flush the datasource pool. Heron asked to hold further resends. |
| 10:07 | `:flush-all-connection-in-pool` executed. Pool `5/5`. |
| 10:08 | Spool drains: 14 messages recovered (`MESSAGE_RECOVERED`), 13 accepted, 1 rejected (another Heron resend). Backlog 0. |
| 10:20 | Emergency config change approved by the IT manager by phone: `max-pool-size` back to 20 until the fix, so a new leak cannot exhaust the pool within the day. |
| 11:05 | Planning office confirms the 126 vehicles are in the plan. Incident resolved; PRB-001 opened. |

## Logs

The sequence for a normal Osprey manifest at 09:41, with the 1.2.0 settings (pool timeout 2 s,
three retries):

```
09:41:03.112 INFO    MESSAGE_RECEIVED channel=REST partner=OSP ref=OSP-MSG-87990 vehicles=18
09:41:03.113 INFO    VALIDATION_SUCCESS shipment=OSP-2026-03288
09:41:05.115 ERROR   DATABASE_TIMEOUT attempt=1/4 reason=no connection available after 2.0s
09:41:05.115 WARNING RETRY_1
09:41:07.617 ERROR   DATABASE_TIMEOUT attempt=2/4 reason=no connection available after 2.0s
09:41:07.617 WARNING RETRY_2
09:41:10.619 ERROR   DATABASE_TIMEOUT attempt=3/4 reason=no connection available after 2.0s
09:41:10.619 WARNING RETRY_3
09:41:14.122 ERROR   DATABASE_TIMEOUT attempt=4/4 reason=no connection available after 2.0s
09:41:14.123 ERROR   MESSAGE_PENDING channel=REST backlog=1
```

Reading it: the message is received and **valid**; only storing it fails, and the reason is the
pool, not an Oracle error. Earlier that morning:

```
Mon 14:12:09.771 WARNING SHIPMENT_CONFLICT partner=OSP shipment=OSP-2026-03251
Tue 07:55:41.508 WARNING SHIPMENT_CONFLICT partner=HRN shipment=HRN-2026-00117
Tue 08:31:02.940 WARNING SHIPMENT_CONFLICT partner=HRN shipment=HRN-2026-00118
Tue 09:02:47.116 WARNING SHIPMENT_CONFLICT partner=HRN shipment=HRN-2026-00116
Tue 09:40:12.331 WARNING SHIPMENT_CONFLICT partner=HRN shipment=HRN-2026-00117
```

## Analysis

Working from the outside in ([runbook R1](../docs/09-operational-runbook.md#r1-messages-are-not-being-processed)):

```
Partner            ✓ messages arrive at the gateway (HTTP 202 back)
  ↓
Gateway / integration layer   ✓ forwarding normally
  ↓
PortFlow application          ✓ running, validating (VALIDATION_SUCCESS)
  ↓
Connection pool               ✗ 0 of 5 available        ← failure
  ↓
Oracle database               ✓ answering queries
```

Five sessions, five conflicts, five connections: every `SHIPMENT_CONFLICT` had cost one
connection. That pointed to the error path of the store operation.

## Impact

- 27 minutes without new manifests in the plan; 14 messages delayed, none lost (spool).
- 126 vehicles missing from the afternoon plan for about 80 minutes; no gate exceptions because
  the plan was complete before the trucks arrived.
- No partner had to resend anything.

## Workaround, resolution, root cause

- **Workaround:** flush the datasource pool; then a larger pool (20) as a temporary buffer.
- **Resolution:** fix released as 1.2.1 on 2026-10-01 through emergency change
  [CR-002](../changes/CR-002-connection-leak-fix.md).
- **Root cause:** on the error path of a database unit of work, the connection was rolled back but
  not returned to the pool. The leak existed since 1.0.0; release 1.2.0 reduced the pool from 20 to
  5, which turned a slow, invisible leak into an outage the first morning a partner resent
  several shipments. Full analysis: [PRB-001](problem-analysis.md).

## Preventive actions

Tracked in PRB-001: release in `finally`, regression test AT-12, pool and backlog alerts, pool
sized with the DBA at 10, soak test for pool configuration changes.

## Replay it

```bash
scripts/simulate-incident.sh
```

Starts the service with the 1.2.0 defect switched back on and a pool of 5, resends a shipment
until the pool is empty, shows the same log sequence, then restarts without the defect and shows
the spool draining. CI runs it on every commit.
