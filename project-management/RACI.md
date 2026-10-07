# RACI

**R** responsible (does the work) · **A** accountable (one per row, decides) ·
**C** consulted (two-way) · **I** informed (one-way).

| Activity | IT Dev Officer | Ops manager | Planners / CS | IT operations | DBA | Integration team | Partner | IT manager | Security |
|---|---|---|---|---|---|---|---|---|---|
| Business requirements | R | **A** | C | I | I | I | C | I | — |
| Functional analysis | **A/R** | C | C | — | — | C | — | I | — |
| Technical specification | **A/R** | I | — | C | C | C | — | I | C |
| Development and unit tests | **A/R** | — | — | — | C | — | — | — | — |
| Database scripts | R | — | — | — | **A** | — | — | — | — |
| Partner mapping review | **A/R** | — | — | — | — | C | C | — | — |
| Partner credentials and routes | C | — | — | C | — | R | C | — | **A** |
| Partner tests | **A/R** | — | — | — | — | C | R | — | — |
| UAT | R | **A** | R | — | — | — | — | I | — |
| Change request to CAB | **R** | C | — | C | C | C | I | **A** | C |
| Deployment to production | C | I | I | **A/R** | R | R | I | I | — |
| Smoke test and go/no-go | **R** | C | — | R | — | — | I | **A** | — |
| Monitoring and alerts | R | — | — | **A** | C | — | — | — | — |
| Second-line support | **A/R** | I | C | C | C | C | C | I | — |
| Problem management | **A/R** | I | — | C | C | C | C | I | — |
| Partner communication (technical) | **A/R** | I | I | — | — | C | — | — | — |
| Benefits measurement | R | **A** | C | — | — | — | — | I | — |

Rule kept throughout: exactly one **A** per activity. Where IT operations and the IT Development
Officer both do work (deployment, monitoring), the platform owner is accountable and the
application owner is responsible for the application part.
