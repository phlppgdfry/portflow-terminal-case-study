# 08 · Release plan: PortFlow 1.3.0

| | |
|---|---|
| Release | 1.3.0 |
| Change | [CR-001 Onboard Gannet Auto Carriers](../changes/CR-001-new-logistics-partner.md) |
| Content | DTM format 303 (UTC offset) support; partner GNT activated; no schema change |
| Window | Tuesday 2026-11-03, 19:00 to 20:00 (low inbound volume, no vessel in the window) |
| Expected downtime | ~5 minutes for the redeploy. Partners are not affected: the integration layer and gateway retry, and duplicates are safe |
| Go/no-go | 2026-11-03 14:00, IT Development Officer with operations manager and IT operations |
| Rollback plan | [rollback-plan.md](../changes/rollback-plan.md) |

The target platform is a WAR on JBoss EAP with Oracle. Commands are shown for that platform;
the demo equivalents are in brackets.

## Before the window

- [ ] CR-001 approved by the CAB (done 2026-10-06)
- [ ] UAT signed off by the operations manager
- [ ] Gannet confirmed its go-live date and has a contact on call during the window
- [ ] Release artifact `portflow-1.3.0.war` built by CI from tag `v1.3.0`; checksum recorded
- [ ] Same artifact deployed and smoke-tested on ACC (no rebuild between ACC and PRD)
- [ ] Database script reviewed: this release has **no DDL**; one DML statement activates GNT
- [ ] Backup verified: last RMAN backup successful (DBA), previous WAR `portflow-1.2.1.war` available
- [ ] Monitoring: alert for GNT rejection rate prepared
- [ ] Business informed: planning office and customer service (e-mail 2026-10-30, reminder on the day)
- [ ] Service desk informed of the window and the rollback contact

## Deployment

| Step | Action | Who | Check |
|---|---|---|---|
| D1 | Announce start in the change channel | IT Development Officer | — |
| D2 | Pause the EDI route to PortFlow in the integration layer (messages queue there) | Integration team | Queue depth grows, no errors |
| D3 | Note the pending backlog: `GET /health` → `pendingBacklog` | IT operations | Must be 0, otherwise wait for the drain |
| D4 | Deploy: `jboss-cli.sh --connect --command="deploy portflow-1.3.0.war --force"` (demo: stop service, check out `v1.3.0`, start) | IT operations | `deployment-info` shows `OK` |
| D5 | Check the log for `SERVICE_STARTED version=1.3.0` and no `ERROR` | IT operations | — |
| D6 | Activate partner: `UPDATE partner SET status = 'ACTIVE' WHERE partner_id = 'GNT'` + commit (demo: `python -m portflow set-partner-status GNT ACTIVE`) | DBA | 1 row updated |
| D7 | Resume the EDI route | Integration team | Queue drains, `MESSAGE_ACCEPTED` in the log |

## Smoke test (S1 to S6)

Run `scripts/smoke-test.sh https://portflow.internal` or by hand:

- [ ] S1 `GET /health` is `UP`, database `UP`, version `1.3.0`
- [ ] S2 a test REST manifest is accepted (test partner, test shipment reference)
- [ ] S3 a test EDI manifest is accepted
- [ ] S4 the shipment is visible via `/api/v1/shipments` (and so in the database)
- [ ] S5 sending it again returns `DUPLICATE`
- [ ] S6 the operations page loads and shows the test messages
- [ ] S7 (this release) Gannet sends one real manifest; arrival time is converted from UTC correctly

Afterwards: remove the smoke-test shipments (support script) and record the result in the change.

## Rollback

Decide within 30 minutes after D4. Criteria: smoke test fails, or `ERROR` events that did not
exist before, or wrong arrival times for any partner.

1. Pause the EDI route (D2).
2. Redeploy the previous artifact: `deploy portflow-1.2.1.war --force`.
3. Set GNT back to `ONBOARDING` so its messages are rejected cleanly instead of mis-parsed.
4. Resume the route; run the smoke test against 1.2.1.
5. Inform Gannet, operations and the CAB.

Details, including why no database rollback is needed for this release:
[rollback-plan.md](../changes/rollback-plan.md).

## After the release

- Hypercare: 5 working days. The IT Development Officer checks the KPIs for GNT every morning
  and has a daily 10-minute call with Gannet in week 1.
- Close CR-001 after 5 days without severity 1 or 2 issues.
- Update [CHANGELOG](../CHANGELOG.md), partner register, and the RAID log.

## Release history

| Version | Date | Content | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-20 | REST channel, Osprey live | Project phase 1 |
| 1.1.0 | 2026-08-24 | EDI channel, Heron live, operations page | Project phase 2 |
| 1.2.0 | 2026-09-24 | KPI endpoint; datasource pool reduced from 20 to 5 at the DBA's request | Standard change |
| 1.2.1 | 2026-10-01 | Connection leak fixed, regression test, pool 10 with alerting | [CR-002 (emergency)](../changes/CR-002-connection-leak-fix.md) |
| 1.3.0 | 2026-11-03 (planned) | UTC arrival times; Gannet onboarding | [CR-001](../changes/CR-001-new-logistics-partner.md) |
