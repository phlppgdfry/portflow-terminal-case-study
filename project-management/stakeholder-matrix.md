# Stakeholder matrix

| Stakeholder | Interest | Influence | What they need from the project | Engagement |
|---|---|---|---|---|
| Operations manager | High | High | Fewer gate exceptions, reliable plan | **Manage closely**: senior user, signs off UAT, monthly board |
| Yard and vessel planners | High | Medium | Correct expected shipments, nothing to retype | Keep informed + involve in UAT; two key users |
| Gate clerks | Medium | Low | Know whether a vehicle is announced | Keep informed: shift briefing per go-live |
| Customer service | High | Low | Explain rejections without IT | Involve: error-code training, `/ops` access |
| IT operations (Unix, middleware) | High | High | Deployable, observable, restartable service | **Manage closely**: senior supplier, release rehearsals |
| DBA | Medium | High | Bounded sessions, reviewed scripts | Involve early: schema review, pool sizing (NFR-09) |
| Integration team | High | Medium | Clear routes per partner, one HTTP target | Involve: weekly working session |
| External partners (Osprey, Heron, Gannet) | High | Medium | Stable interface, quick feedback, predictable onboarding | Partner calls weekly during onboarding; interface agreement |
| IT manager (sponsor) | Medium | High | Benefits, budget, a reusable pattern | **Manage closely**: monthly highlight report |
| Security officer | Medium | High | Controlled external connections | Consult per new partner (AS2, sender binding) |
| TOS vendor | Medium | Medium | Clear IF-04 requirements for phase 3 | Keep informed; formal request for phase 3 |
| Service desk | Medium | Low | First checks and escalation path | Knowledge article per release |

```
            Influence
              ▲
       High   │  Keep satisfied            Manage closely
              │  (DBA, security)           (ops manager, IT ops, sponsor)
              │
       Medium │  Monitor                   Involve / keep informed
              │  (TOS vendor)              (planners, integration team, partners)
              │
       Low    │  Monitor                   Keep informed
              │                            (gate, customer service, service desk)
              └──────────────────────────────────────────────►  Interest
                       Low/Medium                   High
```

## How the stakeholders were connected

The hardest moment was pool sizing after INC-001: the DBA wanted fewer sessions, IT operations
wanted headroom, operations wanted no repeat. The way out was a number everyone could check: the
measured peak of 3 concurrent units of work, which made 10 connections defensible to all three
([D-009](decision-log.md)).
