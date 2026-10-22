# PortFlow · Terminal Application & Integration Case Study

[![CI](https://github.com/phlppgdfry/portflow-terminal-case-study/actions/workflows/ci.yml/badge.svg)](https://github.com/phlppgdfry/portflow-terminal-case-study/actions/workflows/ci.yml)

This repository shows how I approach **application development and application management in a
logistics terminal environment**: from a business problem to requirements, technical design,
integration, database, testing, release, and the incidents and changes that follow once it runs.

It is one story, not a collection of documents. A vehicle terminal in Zeebrugge receives vehicle
announcements from logistics partners over REST and EDI. Wrong data was only discovered at the
gate. PortFlow validates every announcement when it arrives, rejects bad ones with clear reasons,
and shows operations what was rejected. Then it has to be supported: an outage caused by a
connection leak, a partner whose software upgrade broke their messages, and a new partner to
onboard.

> **Fictional case.** The terminal, partners, figures and incidents are invented for this
> portfolio. They are modelled on how vehicle terminals typically work, not on any specific
> company's systems.

## The lifecycle, and where each step lives

```
Business need ─► Requirements ─► Design ─► Integration ─► Database ─► Build ─► Test ─► Release ─► Operate ─► Incident / Problem / Change
```

| Step | Deliverable |
|---|---|
| Business need | [01 · Business context](docs/01-business-context.md) |
| Requirements | [02 · Business requirements](docs/02-business-requirements.md): rules, user stories, FR/NFR with IDs |
| Analysis | [03 · Functional analysis](docs/03-functional-analysis.md): to-be process, message life cycle, screens |
| Specification | [04 · Technical specification](docs/04-technical-specification.md): the *lastenboek*, with traceability |
| Architecture | [05 · Architecture](docs/05-architecture.md) · [context](architecture/system-context.md) · [flow](architecture/integration-flow.md) · [deployment](architecture/deployment-view.md) · [data](architecture/data-flow.md) |
| Integration | [06 · Integration design](docs/06-integration-design.md) · [OpenAPI](integrations/openapi.yaml) · [EDI mapping](integrations/mapping-specification.md) · [error scenarios](integrations/error-scenarios.md) |
| Database | [Data model](database/data-model.md) · [schema.sql](database/schema.sql) · [diagnostic queries](database/diagnostic-queries.sql) (Oracle, run in CI) |
| Build | [`service/`](service/): working integration service plus terminal-event reference model; 52 automated tests |
| Test | [07 · Testing strategy](docs/07-testing-strategy.md) · [test plan](testing/test-plan.md) · [acceptance tests](testing/acceptance-tests.md) · [regression](testing/regression-checklist.md) |
| Release | [08 · Release plan](docs/08-release-plan.md) · [rollback plan](changes/rollback-plan.md) · [CHANGELOG](CHANGELOG.md) |
| Operate | [09 · Runbook](docs/09-operational-runbook.md) · [10 · Infrastructure & app server](docs/10-infrastructure-and-application-server.md) · [11 · Reporting & KPIs](docs/11-reporting-and-kpis.md) |
| Incidents | [INC-001 connection pool exhausted](incidents/INC-001-edi-processing-failure.md) · [INC-002 partner format change](incidents/INC-002-partner-date-format-change.md) · [problem analysis](incidents/problem-analysis.md) |
| Changes | [CR-001 onboard a new partner](changes/CR-001-new-logistics-partner.md) · [CR-002 emergency fix](changes/CR-002-connection-leak-fix.md) · [impact analysis](changes/impact-analysis.md) · [12 · Partner onboarding](docs/12-partner-onboarding.md) |
| Project | [Brief](project-management/project-brief.md) · [stakeholders](project-management/stakeholder-matrix.md) · [RACI](project-management/RACI.md) · [RAID](project-management/RAID-log.md) · [decisions](project-management/decision-log.md) |

**Short on time?** The [five-minute walkthrough](docs/walkthrough.md) picks eight files in order.
The [role mapping](docs/role-mapping.md) links each responsibility of an IT Development Officer
to its evidence here.

## Fictional case timeline (snapshot: 2026-10-07)

| | |
|---|---|
| Service in the fictional scenario | 1.2.1 in production · Osprey (REST) and Heron (EDI) live; no actual production deployment is claimed |
| Project | Phase 4 of 5 · ~80 % · on track |
| Open change | [CR-001](changes/CR-001-new-logistics-partner.md) Gannet onboarding: approved, in UAT, go-live 2026-11-03 |
| Last incident | [INC-002](incidents/INC-002-partner-date-format-change.md) resolved; [PRB-002](incidents/problem-analysis.md#prb-002-partner-changes-reach-us-as-incidents) open (partner change notice) |
| Last problem closed | [PRB-001](incidents/problem-analysis.md#prb-001-recurring-database-connection-exhaustion) connection leak, fixed in 1.2.1 |

## New: executable terminal-event contract

Trace one synthetic vehicle from **gate → yard → customs hold → release → departure**.
The reference model rejects a held departure, safely replays duplicate evidence and detects
changed IDs and out-of-order events. This complements the announcement API with a separate,
standalone event model.

```bash
python3 scripts/replay-terminal-events.py
```

[Contract and scenario](integrations/terminal-event-contract.md) ·
[Fixture](integrations/sample-terminal-events.json) ·
[Reproduced output](testing/terminal-event-evidence.json) ·
[Acceptance tests](service/tests/test_terminal_events.py)

## Run it

Python 3.12 or later, nothing to install.

```bash
cd service
python3 -m portflow serve                     # API + operations page on http://127.0.0.1:8080/ops
python3 -m unittest discover -s tests         # unit, service and API tests

cd ..
scripts/smoke-test.sh                         # the post-deployment smoke test from the release plan
scripts/simulate-incident.sh                  # replays INC-001: leak → pool empty → pending → fix → drain
```

CI runs all of the above on every commit, plus [`scripts/oracle-validate.sh`](scripts/oracle-validate.sh),
which executes the schema, sample data and diagnostic queries on Oracle Database Free.

## What the code is for

The service is small on purpose. It exists to prove the design works, not to be a product:

- REST and EDI (EDIFACT syntax with release characters, segment counts, envelope checks) mapped onto one canonical model;
- business rules returned all at once, whole-manifest rejection, idempotent resends;
- a bounded connection pool that behaves like an application-server datasource, and a spool so
  no message is lost when the database is unavailable;
- the exact log events the runbook and incident reports refer to.

It runs on SQLite so anyone can start it in one command. The Oracle DDL is the target design and is
validated separately. How the demo maps to JBoss EAP, Oracle and an iWay-type integration layer is
in [05 · Architecture](docs/05-architecture.md#target-landscape-and-demo).

## Repository map

```
docs/                 business context → requirements → analysis → spec → architecture → integration
                      → testing → release → runbook → infrastructure → reporting → onboarding
architecture/         Mermaid views: context, integration flow, deployment, data flow
database/             Oracle schema, sample data, diagnostic and DBA queries, data model
integrations/         OpenAPI, EDI mapping spec, sample messages, error scenarios
incidents/            INC-001, INC-002, problem analysis (PRB-001, PRB-002)
changes/              CR-001 (normal), CR-002 (emergency), impact analysis, rollback plan
testing/              test plan, acceptance tests, regression checklist
project-management/   brief, stakeholders, RACI, RAID, decision log
service/              Python reference implementation and tests
scripts/              smoke test, incident replay, Oracle validation, link check
site/                 one-page overview (open site/index.html)
```

## Nederlandstalige samenvatting

Deze repository toont hoe ik applicatieontwikkeling en applicatiebeheer aanpak in een
terminalomgeving: van de vraag van de business naar requirements, technisch lastenboek,
architectuur, integratie (REST en EDI), Oracle-databank, testen, release, en de
tweedelijnssupport daarna. Eén fictieve case over een voertuigterminal in Zeebrugge loopt door
alle documenten: een kleine werkende integratieservice, twee incidenten met probleemanalyse, een
change request voor het aansluiten van een nieuwe logistieke partner, en het projectbeheer
(RACI, RAID, beslissingen) eromheen.
