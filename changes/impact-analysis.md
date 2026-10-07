# Impact analysis · CR-001 Gannet onboarding

Every area the change could touch, checked before the CAB. Blank areas are not skipped: they say
"no impact" and why.

| Area | Impact | Assessment |
|---|---|---|
| **Business process** | Planning office no longer retypes Gannet manifests; customer service handles Gannet rejections | Positive. Customer service briefed on the error codes (2026-10-20) |
| **Users** | Planners see Gannet shipments like any other | No training needed beyond a short note |
| **Application code** | `mapping.parse_edi_arrival`: new branch for format 303 | Small, isolated; 203 and 102 paths unchanged and covered by existing tests |
| **Interfaces** | IF-02 gets one new accepted value (DTM 303); MIG version 1.2 → 1.3 | Backward compatible: nothing that was accepted is now rejected |
| **Database** | One `UPDATE` on `PARTNER`. No DDL, no data migration | Rollback = set status back. Volume: +350 vehicles/week, negligible |
| **Integration layer** | New AS2 profile and route for sender `GNT` | Independent of other routes; can be disabled on its own |
| **Infrastructure** | No new servers. Firewall rule for Gannet's AS2 endpoint | Firewall change FW-2291 linked; lead time 2 weeks |
| **Security** | New external party; certificate-based AS2; sender id bound to profile | Approved by the security officer |
| **Performance** | Gannet peaks: ~350 vehicles once a week | Well within NFR-02/03 (tested up to 1,000 vehicles per manifest) |
| **Monitoring** | GNT appears in rejection-rate and silent-partner alerts automatically | Silent-partner alert muted for GNT until first live call (weekly, not daily) |
| **Reporting** | GNT appears in `V_PARTNER_QUALITY` automatically | None needed |
| **Support** | Partner register, contacts, known issues | Runbook and partner register updated before go-live |
| **Documentation** | MIG 1.3, CHANGELOG, partner register | Part of the release checklist |
| **Contract** | Interface agreement incl. change-notice clause (PRB-002) | Signed 2026-09-29 |
| **Downtime** | ~5 minutes for redeploy | Window with no vessel; messages queue in the integration layer |

## Dependencies

| Dependency | Owner | Needed by | Status |
|---|---|---|---|
| AS2 certificate exchange | Integration team + Gannet | 2026-10-10 | Done 2026-10-02 |
| Firewall FW-2291 | Network team | 2026-10-10 | Done |
| Gannet test availability (P7, P8) | Gannet IT | 2026-10-14 | Confirmed |
| UAT key users | Operations | 2026-10-20 | Confirmed |

## Conclusion

Low technical risk: one isolated parser branch and configuration. The main risk is a wrong time
conversion, covered by daylight-saving test cases and a live check (S7) at go-live. Recommended
for approval.
