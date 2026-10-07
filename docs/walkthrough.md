# Walkthrough: the case in five minutes

Eight stops, in the order the work happens. Each stop is one file and one point.

| # | Open | The point |
|---|---|---|
| 1 | [02 · Business requirements](02-business-requirements.md) | Business problem → rules → requirements with IDs. Every later file refers back to these IDs. |
| 2 | [05 · Architecture](05-architecture.md) | Why each component exists, and what the demo stands for in a JBoss / Oracle / iWay landscape. |
| 3 | [06 · Integration design](06-integration-design.md) | REST and EDI onto one canonical model; idempotency; what happens when the database is down. |
| 4 | [diagnostic-queries.sql](../database/diagnostic-queries.sql) | How second line investigates with data: Q1 rejections per partner, Q3 flow gaps, Q8 data quality. Runs on Oracle in CI. |
| 5 | [INC-001](../incidents/INC-001-edi-processing-failure.md) | An incident worked from the outside in, with the real log sequence, then [PRB-001](../incidents/problem-analysis.md) and five whys. |
| 6 | [CR-001](../changes/CR-001-new-logistics-partner.md) | Onboarding a partner as a change: scope, impact, security, tests, risk, approval. |
| 7 | [Acceptance tests](../testing/acceptance-tests.md) | Requirements as Given / When / Then, each linked to an automated test. |
| 8 | [Release plan](08-release-plan.md) + [rollback](../changes/rollback-plan.md) | Checklist, smoke test, rollback criteria decided before the window. |

## Live demo (two minutes)

```bash
cd service && python3 -m portflow serve          # terminal 1
open http://127.0.0.1:8080/ops                   # operations page

# terminal 2, from the repository root
curl -s -H 'Content-Type: application/json' \
     -d @integrations/sample-vehicle-import.json \
     http://127.0.0.1:8080/api/v1/vehicle-manifests          # 201 ACCEPTED
curl -s -H 'Content-Type: text/plain' \
     --data-binary @integrations/sample-edi-invalid.edi \
     http://127.0.0.1:8080/api/v1/edi-messages               # 422 with two reasons
```

Then, in the operations page, filter on **Rejected** and open the message: that is FR-005, what
customer service sees.

```bash
scripts/simulate-incident.sh     # INC-001 in 20 seconds: leak, pool 0/5, pending, fix, drain
```

## Questions this case is built to answer

- *How do you go from a vague complaint to a requirement?* → stop 1, the success measures table.
- *What do you do when "the EDI doesn't work"?* → runbook R1, then INC-001 as an example.
- *How do you onboard a partner without breaking the others?* → CR-001 impact analysis and regression.
- *What if the release goes wrong?* → rollback criteria and the 30-minute decision window.
- *What don't you know yet?* → [role mapping](role-mapping.md), last table.
