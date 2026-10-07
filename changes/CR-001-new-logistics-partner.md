# CR-001 · Onboard Gannet Auto Carriers as EDI partner

| | |
|---|---|
| Type | Normal change |
| Requested by | Operations manager (commercial agreement with Gannet signed 2026-09-15) |
| Change owner | IT Development Officer |
| Status | **Approved** by CAB 2026-10-06 · in UAT · go-live planned 2026-11-03 |
| Release | PortFlow 1.3.0 ([release plan](../docs/08-release-plan.md)) |
| Risk | Low to medium (see below) |

## Business reason

Gannet Auto Carriers starts a weekly service to Zeebrugge from November, about 350 vehicles per
call. Without integration, the planning office would retype Gannet's manifests: ~3 hours per
call, and the error rate that the project was started to remove.

## Scope

| In scope | Out of scope |
|---|---|
| Gannet as EDI partner on VMANIF | REST channel for Gannet |
| Support for DTM format 303 (time with UTC offset): Gannet's system works in UTC | Other partners switching to 303 (possible, not planned) |
| AS2 connection and route in the integration layer | Outbound messages to Gannet |
| Partner registration and activation | Changes to the TOS |

The mapping review ([onboarding step 4](../docs/12-partner-onboarding.md)) found one gap: Gannet
sends UTC times. Every other field matches the standard format.

## Systems affected

| System | Change | Downtime |
|---|---|---|
| PortFlow | 1.3.0: format 303 in `parse_edi_arrival`; partner GNT activated | ~5 min redeploy |
| Oracle | `UPDATE partner SET status = 'ACTIVE'` for GNT. No DDL. | None |
| Integration layer | New AS2 partner profile and route for sender `GNT` | None (new route) |
| API gateway | None | — |
| Firewall | Inbound AS2 from Gannet's IP range to the DMZ | None |

Full assessment: [impact analysis](impact-analysis.md).

## Security impact

- New external connection: AS2 with certificate exchange; Gannet's certificate validated by the
  security officer, expiry date in the certificate register.
- The integration layer only accepts sender id `GNT` on Gannet's AS2 profile, so Gannet cannot
  announce vehicles under another partner's code.
- No new personal data (checked against Gannet's sample files: VINs and shipment data only).

## Testing

| # | Test | Expected | Result |
|---|---|---|---|
| T1 | Unit: format 303 conversion, summer and winter time | 11:30 UTC → 13:30 (Oct) / 12:30 (Dec) | ✅ automated |
| T2 | Unit: `+` not released in 303 | `V-ARRIVAL-DATE` | ✅ automated |
| T3 | Service: GNT rejected while `ONBOARDING`, accepted after activation (AT-09) | as stated | ✅ automated |
| T4 | Regression: full automated suite + [regression checklist](../testing/regression-checklist.md) | all green | ✅ 2026-10-07 |
| T5 | Partner test set P1 to P8 on ACC ([onboarding](../docs/12-partner-onboarding.md#partner-test-set-minimum)) | as listed | 🔄 P1 to P6 passed, P7 and P8 planned 2026-10-14 |
| T6 | UAT: planners check three Gannet shipments on ACC | arrival times and vehicles correct | ⏳ planned 2026-10-20 |
| T7 | Smoke test on PRD incl. S7 | green | ⏳ go-live |

First partner test (2026-10-02) failed on T5-P1: Gannet's file had `+00` without the release
character. Fixed on Gannet's side the same day; added to the partner test set.

## Risk

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Wrong time conversion puts Gannet vehicles in the wrong planning slot | Low | High | T1 with DST cases; S7 checks a real Gannet message at go-live |
| Change to the EDI parser breaks Heron | Low | High | Format 203 path unchanged; regression on Heron samples; rollback in 10 min |
| AS2 certificate or firewall not ready on time | Medium | Medium (go-live moves) | Requested 2026-09-18; status checked weekly in the RAID log |
| Gannet sends higher volumes than announced | Low | Low | NFR-03 headroom; KPI check in hypercare |

## Deployment and rollback

[Release plan 1.3.0](../docs/08-release-plan.md) · [rollback plan](rollback-plan.md).
Rollback takes about 10 minutes and needs no database restore.

## Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Change owner | IT Development Officer | Submitted | 2026-10-01 |
| Business owner | Operations manager | Approved | 2026-10-03 |
| IT operations | Middleware lead | Approved | 2026-10-05 |
| Security | Security officer | Approved (AS2, sender binding) | 2026-10-05 |
| CAB | IT manager (chair) | **Approved**, condition: T5 and T6 passed before the go/no-go on 2026-11-03 | 2026-10-06 |
