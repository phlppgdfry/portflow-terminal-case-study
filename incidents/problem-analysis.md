# Problem analysis

An incident is restored when the service works again. A problem is closed when we know why it
broke and have made it unlikely to happen again. Two problem records came out of September and
October.

## PRB-001 · Recurring database connection exhaustion

| | |
|---|---|
| Related incident | [INC-001](INC-001-edi-processing-failure.md) |
| Opened / closed | 2026-09-29 / 2026-10-06 |
| Owner | IT Development Officer |
| Status | Closed: root cause fixed in 1.2.1, all actions done |

### Was it recurring?

Yes. After INC-001 the logs since 1.0.0 were searched for `SHIPMENT_CONFLICT` and compared with
pool statistics. Each conflict had leaked one connection since July. With a pool of 20 and the
weekly Sunday restart of the application server, the pool never ran out: at most 6 leaked
connections in one week. Release 1.2.0 reduced the pool to 5; the first busy morning with
resends emptied it.

### Five whys

```
Why were partner messages not stored?
→ No database connection was available; every attempt ended in DATABASE_TIMEOUT.

Why was no connection available?
→ All five pooled connections were borrowed and never returned.

Why were they never returned?
→ When a unit of work raised an error (the unique-key violation on SHIPMENT), the code rolled
  back but skipped returning the connection to the pool.

Why did the code skip it?
→ The release was on the success path only, not in a `finally`. Code review looked at the
  business logic of the conflict handling, not at resource handling on the error path.

Why did no test or alert catch it?
→ No test ran the error path more than once or checked the pool afterwards, and pool usage was
  not monitored. The weekly restart hid the slow leak.
```

### Contributing factors

| Factor | Why it mattered |
|---|---|
| Pool reduced 20 → 5 in 1.2.0 without a soak test | Turned a slow leak into an outage within days |
| Weekly restart of the application server | Masked the leak for two months |
| No pool or backlog alert | First signal came from a partner, not from monitoring |
| Partner resends after rotation changes | Frequent trigger of the error path (legitimate behaviour) |

### What went well

- No message was lost: the spool did its job, and no partner had to resend.
- The log events made the diagnosis quick: valid messages, failed storage, pool empty, database fine.

### Actions

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| A1 | Return the connection in `finally` on every path | IDO | 2026-10-01 | Done (1.2.1, [CR-002](../changes/CR-002-connection-leak-fix.md)) |
| A2 | Regression test: pool complete after repeated failures (AT-12) | IDO | 2026-10-01 | Done |
| A3 | Alerts: backlog > 0 for 5 min; pool < 2 free for 5 min | IDO + monitoring | 2026-10-02 | Done |
| A4 | Pool size from measurement: peak 3 concurrent units of work → `max-pool-size` 10, agreed with the DBA (NFR-09) | IDO + DBA | 2026-10-02 | Done |
| A5 | Changes to pool or timeout settings need a 4-hour soak test on ACC | IDO | 2026-10-03 | Done ([regression checklist](../testing/regression-checklist.md)) |
| A6 | JBoss connection leak detection switched on in ACC | Middleware | 2026-10-03 | Done |
| A7 | Review every other database call for the same pattern | IDO | 2026-10-06 | Done, none found |

## PRB-002 · Partner changes reach us as incidents

| | |
|---|---|
| Related incident | [INC-002](INC-002-partner-date-format-change.md) |
| Opened | 2026-10-05 |
| Owner | IT Development Officer, with the partner managers |
| Status | Open: contractual action in progress |

### Root cause

There is no agreement that partners announce changes to their side of the interface. The
technical controls worked (the bad data was rejected immediately and clearly); the gap is
organisational: nobody was told, and nobody was watching the rejections at 06:00.

### Actions

| # | Action | Owner | Status |
|---|---|---|---|
| B1 | Rejection-spike alert per partner | IDO | Done 2026-10-06 |
| B2 | Interface agreement clause: 10 working days notice of format changes, test slot on ACC | IDO + partner managers | In progress; Gannet's agreement ([CR-001](../changes/CR-001-new-logistics-partner.md)) already has it |
| B3 | Add the clause to the onboarding procedure | IDO | Done ([12 · Partner onboarding](../docs/12-partner-onboarding.md)) |
| B4 | Per EDI partner: who reads negative notices, and from what time | Customer service | Open |
