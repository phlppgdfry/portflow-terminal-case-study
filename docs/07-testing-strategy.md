# 07 · Testing strategy

How testing is organised for PortFlow, from a developer's unit test to the operations manager's
sign-off. The plan for the current release is in [test plan](../testing/test-plan.md); the
acceptance cases are in [acceptance tests](../testing/acceptance-tests.md).

## Test levels

| Level | Question it answers | Who | How | Where |
|---|---|---|---|---|
| Unit | Does each rule and parser do what the spec says? | Developer | Automated, every commit | `service/tests/test_mapping.py`, `test_validation.py` |
| Service / integration | Do parse, validate and store work together, also when the database fails? | Developer | Automated, every commit | `test_service.py` |
| Contract | Does the HTTP API behave as `openapi.yaml` says? | Developer | Automated, every commit | `test_api.py` |
| Database | Does the Oracle DDL run, and do the support queries work? | Developer + DBA | Automated in CI on Oracle Database Free | `scripts/oracle-validate.sh` |
| Partner integration | Does this partner's real test file pass end to end? | IT Development Officer + partner | Partner sends test messages to ACC | [CR-001 test cases](../changes/CR-001-new-logistics-partner.md#testing) |
| UAT | Can operations do their job with it? | Key users, led by the operations manager | Scripted scenarios on ACC | [acceptance tests](../testing/acceptance-tests.md) |
| Regression | Did we break something that used to work? | Automated suite + checklist | Before every release | [regression checklist](../testing/regression-checklist.md) |
| Smoke | Is the deployment alive and wired correctly? | Whoever deploys | After every deployment, 2 minutes | `scripts/smoke-test.sh` |
| Failure replay | Does the system behave as designed when the known failure happens again? | Developer | Automated in CI | `scripts/simulate-incident.sh` |
| Performance | Do we meet NFR-02 and NFR-03? | Developer + IT operations | Before go-live and after major changes | Load test on ACC with 1,000-vehicle manifests |

The pyramid is deliberate: most checks are cheap and automatic; the expensive human tests (UAT,
partner tests) focus on what only humans or partners can judge.

## Test cases that matter most

These come straight from the business rules and the incidents:

| Scenario | Expected result | Covered by |
|---|---|---|
| Valid manifest | Accepted, shipment and vehicles stored | AT-01, AT-02 |
| Missing VIN | Rejected, `V-REQUIRED` on that vehicle | AT-03 |
| Unknown partner | Rejected, `V-PARTNER-UNKNOWN` | AT-04 |
| Duplicate message | Ignored, original id returned | AT-05 |
| Shipment resent under new reference | Rejected, `V-SHIPMENT-EXISTS` | AT-06 |
| Database unavailable | Pending, processed after recovery | AT-07 |
| Invalid JSON / truncated EDI | Rejected, `E-SYNTAX`, payload kept | AT-08 |
| Error path many times in a row | Pool fully available afterwards | AT-12 (PRB-001) |
| Partner sends date-only arrival | Rejected, `V-ARRIVAL-DATE` | `test_date_only_format_is_rejected` (INC-002) |

## Environments

| Env | Purpose | Data | Who deploys |
|---|---|---|---|
| DEV | Development, unit tests | Synthetic | Developer |
| TST | Integration tests with the integration layer | Synthetic + anonymised samples | Developer |
| ACC | Partner tests, UAT, performance, release rehearsal | Copy of production reference data, partner test files | IT operations (same procedure as PRD) |
| PRD | Production | Real | IT operations, after CAB approval |

ACC is deployed with exactly the same procedure as production, so the deployment itself is
tested before it matters.

## Entry and exit criteria

| | Entry | Exit |
|---|---|---|
| UAT | Automated suite green; smoke test green on ACC; test data loaded; key users available | All Must cases passed; no open severity 1 or 2 defects; sign-off by operations manager |
| Partner test | Partner configured on ACC; credentials issued; mapping reviewed | Partner's valid file accepted; partner's broken files rejected with the expected codes |
| Release | UAT signed; partner test passed; release notes and rollback plan reviewed | Smoke test green on PRD; hypercare started |

## Defect severity

| Sev | Definition | Example | Release blocker |
|---|---|---|---|
| 1 | Data loss or no processing at all | Accepted message not stored | Yes |
| 2 | A Must requirement fails, no workaround | Duplicate processed twice | Yes |
| 3 | Requirement fails, workaround exists | KPI tile shows wrong number | Decided at go/no-go |
| 4 | Cosmetic | Typo on the operations page | No |

## Test data

- Sample files live next to the specification in [`integrations/`](../integrations/), and the
  automated tests read **those files**. If the spec example changes, the tests notice.
- VINs are invented but follow the ISO 3779 format rules.
- Oracle sample data uses relative timestamps so the diagnostic queries always return rows.
