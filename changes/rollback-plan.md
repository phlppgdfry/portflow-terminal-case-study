# Rollback plan · PortFlow 1.3.0

| | |
|---|---|
| Applies to | Release 1.3.0 ([CR-001](CR-001-new-logistics-partner.md)) |
| Decision window | Up to 30 minutes after deployment step D4; later = fix forward unless severity 1 |
| Decided by | IT Development Officer with the operations shift lead; IT manager informed |
| Duration | ~10 minutes |
| Data loss | None |

## When to roll back

- Smoke test S1 to S6 fails and cannot be fixed within 15 minutes.
- New `ERROR` events that did not occur before the release (other than one-off timeouts).
- Arrival times wrong for any partner (S7 or a planner's report).
- Any accepted message not visible in the database.

Do **not** roll back for: a Gannet data error (that is a rejection, working as designed), or a
Gannet connection problem (disable the route instead).

## Steps

| # | Step | Command / action | Check |
|---|---|---|---|
| RB1 | Announce rollback in the change channel | — | — |
| RB2 | Pause the EDI route to PortFlow | Integration layer console | Queue grows, no errors |
| RB3 | Set Gannet back to onboarding | `UPDATE partner SET status = 'ONBOARDING' WHERE partner_id = 'GNT'; COMMIT;` | 1 row |
| RB4 | Redeploy the previous artifact | `jboss-cli.sh --connect --command="deploy /opt/releases/portflow-1.2.1.war --force"` | `deployment-info` OK |
| RB5 | Check the start-up log | `SERVICE_STARTED version=1.2.1`, no `ERROR` | — |
| RB6 | Resume the EDI route | Integration layer console | Queue drains |
| RB7 | Smoke test S1 to S6 | `scripts/smoke-test.sh <url>` | All PASS |
| RB8 | Inform Gannet, operations, CAB | E-mail template "release rolled back" | — |

## Why no database rollback is needed

1.3.0 has no DDL. The only data change is Gannet's status, reversed in RB3. Shipments that Gannet
announced while 1.3.0 was live stay valid: 1.2.1 can read them, and their arrival times were
already converted to local time on the way in.

If a Gannet shipment was stored with a **wrong** time (the rollback trigger), list them with:

```sql
SELECT s.shipment_ref, s.expected_arrival, m.raw_payload
  FROM shipment s JOIN edi_message m ON m.message_id = s.message_id
 WHERE s.partner_id = 'GNT';
```

Customer service asks Gannet to resend them after the fix; the wrong shipments are cancelled in
the TOS. No manual `UPDATE` on shipment times: corrections always come from the partner.

## For releases with a schema change

Not the case for 1.3.0, but the standard is: every DDL script has a reviewed reverse script, the
DBA takes a restore point (`CREATE RESTORE POINT before_portflow_x_y_z GUARANTEE FLASHBACK DATABASE`)
before the change, and additive changes (new columns, new tables) are preferred so the previous
version keeps working without a reverse script.
