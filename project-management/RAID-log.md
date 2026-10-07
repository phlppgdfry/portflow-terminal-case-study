# RAID log

Risks, assumptions, issues and dependencies. Reviewed in the weekly working session; the top 5
go into the monthly highlight report. Status as of 2026-10-07.

## Risks

| ID | Risk | Probability | Impact | Owner | Mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | Partners cannot change their side in time | Medium | High | IDO | Keep their EDI flows; strict but clear errors; test slots booked early | Reduced: 2 of 3 live |
| R-02 | Oracle session limits reached by the new service | Medium | High | IDO + DBA | Bounded pool, sized with the DBA (NFR-09) | **Occurred** (INC-001) → closed via PRB-001 |
| R-03 | Key-person dependency: one developer knows the parser | Medium | Medium | IT manager | Spec + tests + pairing with integration team | Open |
| R-04 | TOS vendor lead time for phase 3 interface | High | Medium | IT manager | Formal request sent 2026-09-01; phase 3 is a separate project | Open |
| R-05 | Gannet AS2 certificate or firewall not ready | Medium | Medium | Integration team | Requested 2026-09-18 | Closed 2026-10-02 |
| R-06 | Partner changes break the interface without notice | Medium | Medium | IDO | Rejection-spike alert; notice clause (PRB-002) | **Occurred** (INC-002) → mitigation in progress |
| R-07 | Wrong time conversion for UTC partner | Low | High | IDO | DST test cases; live check S7 | Open until go-live |

## Assumptions

| ID | Assumption | Validated |
|---|---|---|
| A-01 | Partners accept whole-manifest rejection | Yes, in interface agreements |
| A-02 | VINs and shipment data contain no personal data | Yes, sample review per partner |
| A-03 | The existing integration layer can host new partner routes without licence change | Yes (integration team, 2026-06-12) |
| A-04 | Peak load is driven by vessel windows: ≤ 10 manifests per minute | Yes, measured since 1.1.0 (peak 6/min) |

## Issues

| ID | Issue | Owner | Action | Status |
|---|---|---|---|---|
| I-01 | INC-001 follow-up actions | IDO | PRB-001 A1 to A7 | Closed 2026-10-06 |
| I-02 | No agreement on partner change notice | IDO | PRB-002 B2 | Open |
| I-03 | Smoke-test shipments remain visible | IDO | Cleanup script; fix in 1.4.0 (KI-02) | Open |

## Dependencies

| ID | Dependency | On | Needed by | Status |
|---|---|---|---|---|
| D-01 | AS2 profile and route for Gannet | Integration team | 2026-10-10 | Done |
| D-02 | Firewall FW-2291 | Network team | 2026-10-10 | Done |
| D-03 | Gannet test slots (P7, P8) | Gannet | 2026-10-14 | Confirmed |
| D-04 | UAT key users | Operations | 2026-10-20 | Confirmed |
| D-05 | TOS interface specification | TOS vendor | Phase 3 | Waiting |
