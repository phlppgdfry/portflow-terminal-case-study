# Project brief · PortFlow partner manifest integration

A PRINCE2-style brief, kept to what a project of this size needs: why, what, who, when, and the
limits within which the project manager may act without going back to the sponsor.

| | |
|---|---|
| Sponsor (Executive) | IT manager |
| Senior user | Operations manager |
| Senior supplier | Head of IT operations |
| Project manager | IT Development Officer |
| Start / planned end | 2026-06-01 / 2026-12-18 |
| Status 2026-10-07 | 🟢 on track · phase 4 of 5 · ~80 % |

## Business case (summary)

| | |
|---|---|
| Problem | ~12 hours per day lost on gate exceptions and retyping caused by unchecked pre-advice ([01](../docs/01-business-context.md)) |
| Benefit | Gate exceptions < 15 per day; no retyping for onboarded partners; partner feedback < 5 minutes |
| Cost (internal effort) | ~95 person-days IT, ~20 person-days operations; integration layer and Oracle licences already in place |
| Payback | Recovered time alone ≈ 1.5 FTE in operations; payback within the first year |
| Main risk | Partners must change how they send data; mitigated by keeping their EDI flows (no rebuild for them) |

## Objectives

1. Validate every inbound manifest from onboarded partners automatically (FR-001 to FR-013).
2. Onboard the three main partners: Osprey (REST), Heron (EDI), Gannet (EDI).
3. Hand over to application management with runbook, monitoring and support procedures.
4. Leave a repeatable onboarding procedure for the next partners.

## Scope

In and out of scope as in [01 · Business context](../docs/01-business-context.md#scope-of-this-case).
The interface to the TOS (pre-advice, IF-04) is a separate follow-up project.

## Phases and milestones

| Phase | Content | Milestone | Date | Status |
|---|---|---|---|---|
| 1. Initiation | Business case, requirements, architecture | Requirements signed off | 2026-06-26 | ✅ |
| 2. REST channel | Service, database, REST, Osprey | 1.0.0 live with Osprey | 2026-07-20 | ✅ |
| 3. EDI channel | EDI parser, integration layer, operations page, Heron | 1.1.0 live with Heron | 2026-08-24 | ✅ |
| 3b. Stabilisation | KPIs, INC-001 follow-up (1.2.1) | PRB-001 closed | 2026-10-06 | ✅ |
| 4. Third partner | Gannet onboarding (CR-001) | 1.3.0 live with Gannet | 2026-11-03 | 🔄 UAT |
| 5. Closure | Benefits baseline, hand-over, lessons learned | Project closed | 2026-12-18 | ⏳ |

## Tolerances

The project manager may decide within these limits; outside them it goes to the sponsor.

| | Tolerance |
|---|---|
| Time | ± 2 weeks per milestone |
| Effort | + 10 % (≈ 10 person-days) |
| Scope | Should / Could stories may move between phases; Must stories may not be dropped |
| Quality | No release with an open severity 1 or 2 defect |

## Governance

| Forum | Who | Frequency | Purpose |
|---|---|---|---|
| Project board | Sponsor, senior user, senior supplier, PM | Monthly + at each phase end | Go / no-go per phase, exceptions |
| Working session | PM, developers, integration team, DBA | Weekly | Progress, blockers, RAID |
| Partner calls | PM, partner IT | Weekly during onboarding | Mapping, tests, go-live |
| CAB | Change manager, IT operations, PM | Weekly | Every production change |

## Communication

| Audience | What | How | When |
|---|---|---|---|
| Project board | Highlight report (status, RAID top 5, decisions needed) | E-mail + meeting | Monthly |
| Operations teams | What changes for them, when | Shift briefing, one-page note | Before each go-live |
| Partners | Interface spec, test plan, go-live date | Partner calls, e-mail | Per onboarding |
| Service desk | What PortFlow is, first checks, escalation | Knowledge article | Before 1.0.0, updated per release |

Related: [stakeholder matrix](stakeholder-matrix.md) · [RACI](RACI.md) ·
[RAID log](RAID-log.md) · [decision log](decision-log.md).
