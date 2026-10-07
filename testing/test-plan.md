# Test plan · PortFlow 1.3.0

Applies the [testing strategy](../docs/07-testing-strategy.md) to release 1.3.0
([CR-001](../changes/CR-001-new-logistics-partner.md)).

## Scope

| In scope | Out of scope |
|---|---|
| DTM format 303 parsing and time conversion | REST channel changes (none in this release) |
| Gannet partner configuration and activation | Performance re-test (no change to the processing path; last run 1.2.1) |
| Regression of all existing behaviour | TOS interface (phase 3) |
| Deployment and rollback procedure on ACC | |

## Approach

| Level | What | Who | When | Status |
|---|---|---|---|---|
| Unit + service + contract | Full automated suite (CI on every commit) | IDO | Continuous | ✅ green |
| Oracle | Schema and queries on Oracle Database Free (CI) | IDO | Continuous | ✅ green |
| Failure replay | INC-001 replay (CI) | IDO | Continuous | ✅ green |
| Partner test | P1 to P8 with Gannet on ACC | IDO + Gannet | 2026-10-02 to 2026-10-14 | 🔄 P1–P6 passed |
| UAT | AT-02, AT-09, AT-10, AT-15 with Gannet files; planners check 3 shipments | Planners, customer service | 2026-10-20 | ⏳ |
| Regression | [Checklist](regression-checklist.md) | IDO | 2026-10-21 | ⏳ |
| Release rehearsal | Deploy, smoke test, **rollback**, redeploy on ACC | IT operations + IDO | 2026-10-22 | ⏳ |

## Test environment

ACC, deployed with the production procedure; Gannet's AS2 test profile pointing to ACC; partner
register copied from production with GNT as `ONBOARDING`.

## Test data

Gannet's three anonymised sample files; the samples in [`integrations/`](../integrations/);
generated 1,000-vehicle manifest for P7.

## Entry and exit criteria

From the [testing strategy](../docs/07-testing-strategy.md#entry-and-exit-criteria), plus for
this release: rollback rehearsed successfully on ACC.

## Defects found so far

| ID | Found in | Description | Severity | Status |
|---|---|---|---|---|
| DEF-031 | P1 | Gannet sends `+00` without release character `?` → `V-ARRIVAL-DATE` | 3 | Fixed by Gannet 2026-10-02; added to partner test set |
| DEF-032 | Review | Ops page showed arrival time without a time-zone hint | 4 | Accepted: page states "local time" in 1.4.0 |

## Risks to testing

| Risk | Mitigation |
|---|---|
| Gannet test availability slips | Agreed slots in the interface agreement; escalation via partner manager |
| UAT key users pulled into operations on a busy day | Two dates booked (10-20 and 10-22) |

## Sign-off

| Role | Sign-off |
|---|---|
| Operations manager | UAT |
| IT Development Officer | Partner test, regression, rehearsal |
| Middleware lead | Release rehearsal |
