# 02 · Business requirements

**Business problem.** Operations staff lose time because wrong vehicle data from logistics
partners is only discovered at the gate and has to be traced by hand
([01 · Business context](01-business-context.md)).

**Business requirement.** The system must validate incoming vehicle data automatically and make
errors visible to operations and to the partner that sent them, before the vehicles arrive.

**Success measures** (reviewed three months after go-live, see the
[project brief](../project-management/project-brief.md)):

| Measure | Baseline | Target |
|---|---|---|
| Gate exceptions caused by pre-advice | ~60 / day | < 15 / day |
| Time from partner sending a bad manifest to partner knowing what is wrong | hours | < 5 minutes |
| Manifests retyped by hand in the planning office | ~30 / day | 0 for onboarded partners |
| Effort to onboard a new partner on the standard format | ~6 weeks | < 3 weeks |

## Stakeholders and their needs

| Stakeholder | Need |
|---|---|
| Operations manager | Fewer gate exceptions; a plan based on correct data |
| Yard and vessel planners | See per shipment what is expected and what has arrived |
| Gate clerks | Know at the gate whether a vehicle was announced |
| Customer service | Tell a partner why a manifest was rejected, without asking IT |
| External logistics partners | A clear interface, quick feedback, a predictable onboarding |
| IT operations / DBA | A service that is observable, restartable, and gentle on the database |
| IT manager (sponsor) | Measurable benefit; a reusable integration pattern |

## Business rules

The codes in brackets are the rejection codes the system returns
([error scenarios](../integrations/error-scenarios.md)).

| ID | Rule |
|---|---|
| BR-01 | A manifest must contain partner, message reference, shipment reference, expected arrival and terminal code (`V-REQUIRED`). |
| BR-02 | Every vehicle has a VIN of 17 characters, digits and capitals, never I, O or Q (`V-VIN-FORMAT`). |
| BR-03 | A VIN appears only once in a manifest (`V-VIN-DUPLICATE`). |
| BR-04 | The manifest is for this terminal, `BEZEE` (`V-TERMINAL`). |
| BR-05 | The expected arrival includes a time of day; the yard plan works in hours, not days (`V-ARRIVAL-DATE`). |
| BR-06 | A manifest holds 1 to 1,000 vehicles (`V-NO-VEHICLES`, `V-TOO-MANY`). |
| BR-07 | Only registered partners with status ACTIVE may announce vehicles (`V-PARTNER-UNKNOWN`, `V-PARTNER-INACTIVE`). |
| BR-08 | A partner uses the channel it was set up for: REST or EDI (`V-PARTNER-CHANNEL`). |
| BR-09 | A shipment reference is announced once per partner (`V-SHIPMENT-EXISTS`). |
| BR-10 | A message that is received twice is processed once (idempotency on partner + message reference). |
| BR-11 | If any rule fails, the whole manifest is rejected. No half shipments ([D-002](../project-management/decision-log.md)). |

## User stories

| ID | Story | Priority (MoSCoW) |
|---|---|---|
| US-01 | As a **partner**, I want to send a manifest over REST and get an immediate answer, so I can correct errors while the data is still in front of me. | Must |
| US-02 | As a **partner on EDI**, I want to keep using my EDI flow, so I do not need to rebuild my integration. | Must |
| US-03 | As a **planner**, I want only valid manifests to reach the plan, so I do not plan on wrong data. | Must |
| US-04 | As **customer service**, I want to see rejected messages with the reason and the original payload, so I can explain the rejection to the partner. | Must |
| US-05 | As **IT operations**, I want no message to be lost when the database is briefly unavailable, so partners do not need to resend. | Must |
| US-06 | As a **gate clerk**, I want to register an arrival by VIN, so expected and arrived can be compared. | Should |
| US-07 | As the **operations manager**, I want daily figures per partner (volumes, rejection rate), so I can discuss data quality with partners. | Should |
| US-08 | As the **IT Development Officer**, I want to onboard a new partner by configuration and a mapping review, so onboarding does not need a project each time. | Should |
| US-09 | As a **partner**, I want to replace a manifest I already sent. | Won't (this phase, [D-008](../project-management/decision-log.md)) |

## Functional requirements

| ID | Requirement | Story | Verified by |
|---|---|---|---|
| FR-001 | The system shall accept vehicle manifests from approved partners over REST (JSON). | US-01 | AT-01 |
| FR-002 | The system shall accept vehicle manifests over EDI (VMANIF) delivered by the integration layer. | US-02 | AT-02 |
| FR-003 | Every vehicle must contain a valid VIN (BR-02, BR-03). | US-03 | AT-03 |
| FR-004 | Invalid messages shall not be processed automatically: no shipment or vehicle is created (BR-11). | US-03 | AT-03, AT-04 |
| FR-005 | Operations users shall be able to view rejected messages with every reason and the raw payload. | US-04 | AT-10 |
| FR-006 | A message received more than once shall be processed once and answered as a duplicate (BR-10). | US-01 | AT-05 |
| FR-007 | A shipment announced a second time under a new message reference shall be rejected (BR-09). | US-03 | AT-06 |
| FR-008 | Only ACTIVE partners on their registered channel are accepted (BR-07, BR-08). | US-08 | AT-09, AT-14 |
| FR-009 | When the database is unavailable, a received message shall be kept and processed automatically once it is back. | US-05 | AT-07 |
| FR-010 | A syntactically unreadable message shall be stored as rejected with its raw payload. | US-04 | AT-08 |
| FR-011 | Gate staff shall be able to register a vehicle arrival by VIN. | US-06 | AT-11 |
| FR-012 | The system shall provide KPIs per partner and per day for reporting. | US-07 | AT-13 |
| FR-013 | Arrival times shall be stored in terminal local time, whatever time zone the partner uses. | US-02 | AT-15 |

## Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Availability | 99.5 % during operating hours (06:00 to 22:00), measured monthly. |
| NFR-02 | Performance | 95 % of manifests up to 1,000 vehicles are answered within 2 seconds. |
| NFR-03 | Capacity | Peaks of 10 manifests per minute without queueing (vessel arrival windows). |
| NFR-04 | Recoverability | No accepted message is lost (RPO 0). Service restored within 1 hour (RTO). |
| NFR-05 | Auditability | Raw payload and outcome of every message kept 90 days. |
| NFR-06 | Security | Partners authenticate at the gateway (API key over TLS, or AS2/SFTP for EDI). The application uses a database account with only the rights it needs. |
| NFR-07 | Observability | Health endpoint, structured log events, alert on backlog and connection pool usage. |
| NFR-08 | Maintainability | A partner on the standard format is onboarded by configuration, without a code change. |
| NFR-09 | Database footprint | At most 10 database sessions for this service (agreed with the DBA, see [PRB-001](../incidents/problem-analysis.md)). |

## Acceptance

The acceptance criteria per requirement are written as test cases in
[acceptance tests](../testing/acceptance-tests.md). The operations manager signs off UAT.

Next: [03 · Functional analysis](03-functional-analysis.md).
