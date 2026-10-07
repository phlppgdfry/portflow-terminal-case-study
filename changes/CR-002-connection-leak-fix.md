# CR-002 · Fix database connection leak (emergency change)

| | |
|---|---|
| Type | **Emergency change**: approved by the emergency CAB (IT manager + operations manager), reviewed at the next regular CAB |
| Trigger | [INC-001](../incidents/INC-001-edi-processing-failure.md), [PRB-001](../incidents/problem-analysis.md) |
| Change owner | IT Development Officer |
| Release | PortFlow 1.2.1 |
| Implemented | 2026-10-01 19:00 to 19:25 |
| Status | Closed 2026-10-06 (5 days without pool alerts) |

## Why emergency and not normal

Until the fix, the pool was held at 20 connections as a temporary workaround, above the 10 the
DBA allows for this service, and every partner resend still leaked a connection. Waiting for the
next regular CAB (2026-10-06) meant five more days of that risk, including a weekend without a
restart.

## Change

| Item | Before | After |
|---|---|---|
| Connection release | On success path only | In `finally`, every path ([`db.py`](../service/portflow/db.py)) |
| Test | None for repeated error paths | AT-12 `test_at12_prb001_pool_is_whole_after_failed_units_of_work` |
| `max-pool-size` | 20 (temporary) | 10 (NFR-09) |
| Monitoring | None on pool or backlog | Alerts on backlog and pool pressure |

## Shortened process, same safeguards

| Normal change step | In this emergency change |
|---|---|
| CAB meeting | Emergency CAB by phone, 2026-09-30 16:00 |
| Full UAT | Not needed: no functional change. Automated suite + INC-001 replay on ACC |
| Partner test | Not needed: interface unchanged |
| Release plan | Standard redeploy steps D1 to D7 and smoke test S1 to S6 |
| Rollback | Redeploy 1.2.0 with pool 20 (the workaround state) |

## Verification

- ACC: INC-001 replay (`scripts/simulate-incident.sh`) with the fix: pool stays complete.
- PRD smoke test green at 19:22.
- 2026-10-01 to 2026-10-06: 9 `SHIPMENT_CONFLICT` events in production, pool usage never above 3.
