# Regression checklist

Run before every release, after the automated suite is green. Ticks are recorded in the change
record. Automated items are checked in the CI run of the release tag.

## Automated (CI on the release tag)

- [ ] Unit, service and contract tests green (`python -m unittest discover -s tests`)
- [ ] Oracle job green: schema, sample data and diagnostic queries run without error
- [ ] INC-001 replay passes: leak reproduced with the fault flag, backlog drains with the fix
- [ ] Smoke test S1 to S6 green against a fresh instance
- [ ] Documentation links check green

## By hand on ACC

**Inbound**
- [ ] REST manifest from each active REST partner accepted
- [ ] EDI manifest from each active EDI partner accepted (one real, anonymised file per partner)
- [ ] Each partner's last known rejected file still gives the same codes
- [ ] Duplicate returns 200 with the original id

**Operations**
- [ ] `/ops` loads; Rejected filter and message detail work
- [ ] Gate arrival updates the expected-shipments list
- [ ] KPI tiles plausible against diagnostic query Q1

**Resilience**
- [ ] Stop the database listener for 2 minutes: messages go `PENDING`, backlog alert fires, backlog drains after restart
- [ ] Pool usage returns to idle level after a burst of 20 manifests

**Configuration changes** (only if the release changes pool, timeout or retry settings, PRB-001 A5)
- [ ] 4-hour soak test on ACC with production-like traffic and at least 10 shipment conflicts
- [ ] Datasource statistics: `InUseCount` back to baseline afterwards

**Operability**
- [ ] Log shows `SERVICE_STARTED` with the new version; no new `ERROR` events at idle
- [ ] `/health` reports the new version
- [ ] Runbook, CHANGELOG and MIG version updated
- [ ] Rollback rehearsed on ACC when the release changes code or configuration
