# Role mapping: IT Development Officer → evidence in this repository

This case study was built around the responsibilities of an **IT Development Officer** in an
international logistics organisation running a Terminal Operating System. The table maps each
responsibility to the file that shows how I approach it.

## Responsibilities

| Responsibility | Evidence |
|---|---|
| Analyse the needs of the business | [01 · Business context](01-business-context.md), [02 · Business requirements](02-business-requirements.md) |
| Translate business needs into technical solutions | [03 · Functional analysis](03-functional-analysis.md), [05 · Architecture](05-architecture.md) |
| Write technical specifications (*technische lastenboeken*) | [04 · Technical specification](04-technical-specification.md), [mapping specification](../integrations/mapping-specification.md), [openapi.yaml](../integrations/openapi.yaml) |
| Write project plans | [Project brief](../project-management/project-brief.md) with phases, milestones, tolerances |
| Write change requests | [CR-001](../changes/CR-001-new-logistics-partner.md) (normal), [CR-002](../changes/CR-002-connection-leak-fix.md) (emergency), [impact analysis](../changes/impact-analysis.md) |
| Follow up IT projects | [RAID log](../project-management/RAID-log.md), [decision log](../project-management/decision-log.md), milestone status |
| Work with internal teams and external partners | [Partner onboarding](12-partner-onboarding.md), [RACI](../project-management/RACI.md), [stakeholder matrix](../project-management/stakeholder-matrix.md) |
| Guide partners through development and implementation | CR-001 partner tests, [error scenarios](../integrations/error-scenarios.md) as partner documentation |
| Point of contact for users of new applications | [Operations page](03-functional-analysis.md#screens), UAT script in [acceptance tests](../testing/acceptance-tests.md) |
| Manage and optimise systems in the TOS environment | [Runbook](09-operational-runbook.md), [diagnostic queries](../database/diagnostic-queries.sql), pool sizing (D-009) |
| Second-line support for incidents and changes | [INC-001](../incidents/INC-001-edi-processing-failure.md), [INC-002](../incidents/INC-002-partner-date-format-change.md), [problem analysis](../incidents/problem-analysis.md) |
| Write test procedures | [Testing strategy](07-testing-strategy.md), [test plan](../testing/test-plan.md), [regression checklist](../testing/regression-checklist.md) |
| Guide implementations | [Release plan](08-release-plan.md), [rollback plan](../changes/rollback-plan.md) |
| Develop an application linked to a database | [`service/`](../service/) with tests; [schema.sql](../database/schema.sql) |
| Optimise algorithms and applications | Bounded pool and retry design, reporting views, index choices in the [data model](../database/data-model.md) |

## Technologies named as a plus

What this repository shows for each, and what it does not prove.

| Technology | Shown here | Not claimed by this repository |
|---|---|---|
| Oracle | Schema with constraints, function-based index, reporting views; support and DBA queries; **all run in CI on Oracle Database Free** | DBA work: backup, tuning, RAC, Data Guard |
| JBoss | Datasource and deployment concepts; CLI commands in runbook and release plan; the demo pool behaves like a JBoss datasource | Hands-on JBoss administration in production |
| iWay | Where the integration layer sits, transport vs business acknowledgement, routing per partner | Building iWay flows |
| EDI | EDIFACT-syntax parser with release character, segment count and envelope checks, tested | Certification on a specific standard message (DESADV, IFTMIN) |
| WebFOCUS | Reporting views as the BI contract, KPI definitions, report design | Building WebFOCUS reports |
| APEX | Where an APEX screen would replace `/ops`, and the trade-off | Building APEX applications |
| IBM Power / AIX | How the stack fits together; first host checks | AIX system administration |
| Project management (PRINCE2 or similar) | Brief with business case and tolerances, board, RAID, decisions, phases | A PRINCE2 certificate |

The point of the repository is not to claim experience I don't have. It shows that I understand
how these parts of an enterprise landscape fit together, that I can learn a stack quickly, and how
I work from a business question to a running, supportable change.
