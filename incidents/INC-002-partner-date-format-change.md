# INC-002 · All Heron manifests rejected after a partner software upgrade

| | |
|---|---|
| Priority | P3: one partner affected, no physical impact yet, workaround via partner |
| Opened / resolved | 2026-10-05 08:50 / 2026-10-05 10:30 |
| Reported by | Yard planner (vessel for tomorrow had no shipments) |
| Handled by | Customer service (first line), IT Development Officer (second line), Heron IT |
| Version | PortFlow 1.2.1 |
| Problem record | [PRB-002](problem-analysis.md#prb-002-partner-changes-reach-us-as-incidents) |

## What happened

Heron upgraded its transport management system over the weekend. The new version's EDI converter
wrote the expected arrival as a date only (`DTM+132:20261006:102`) instead of date and time
(`DTM+132:202610061400:203`). PortFlow rejected every Heron manifest with `V-ARRIVAL-DATE`, exactly
as specified. Heron's system received the negative notices, but nobody at Heron monitors them at
06:00 on a Monday.

The system worked. The **process** around partner changes did not.

## Timeline

| Time | What happened |
|---|---|
| Sat 10-03 | Heron upgrade (not announced to the terminal) |
| 06:10 | First Heron manifest of the week rejected, `V-ARRIVAL-DATE` |
| 06:10 to 08:30 | 14 Heron manifests rejected (512 vehicles). Other partners normal. |
| 08:40 | Planner: tomorrow's Heron vessel has no shipments. Calls customer service. |
| 08:50 | Customer service: `/ops`, filter Rejected, partner HRN: same code on every message since 06:10. Escalates to second line (pattern from [runbook R2](../docs/09-operational-runbook.md#r2-a-partner-gets-many-rejections), step 3). |
| 09:05 | IDO compares the raw payload with an accepted Heron message from last week: only the DTM format changed, 203 → 102. Calls Heron IT. |
| 09:30 | Heron confirms the upgrade changed the date mapping default. |
| 09:35 | Decision: no change on the terminal side. A date without time cannot be planned ([D-006](../project-management/decision-log.md)). Heron restores format 203. |
| 10:05 | Heron fixes the mapping and resends the 14 manifests with new interchange references. |
| 10:30 | All 14 accepted. Planner confirms tomorrow's vessel is complete. Resolved. |

## Evidence

Diagnostic query Q2 at 08:55:

```
PARTNER_ ERROR_CODE           OCCURRENCES LAST_SEEN
-------- -------------------- ----------- -------------------
HRN      V-ARRIVAL-DATE                14 2026-10-05 08:30:12
```

One partner, one code, every message since a fixed moment: a change, not a data error.

Before and after:

```
last week   DTM+132:202609291400:203'
today       DTM+132:20261006:102'
```

## Impact

- 512 vehicles announced 2 h 20 min late. The vessel arrived the next day, so no gate impact.
- Without the planner's check, the problem would have been found at the next day's vessel call.

## Why the resends were not blocked

Rejected manifests never create a shipment, so the corrected messages did not hit BR-09
(`V-SHIPMENT-EXISTS`). This is the reason for whole-manifest rejection ([D-002](../project-management/decision-log.md)).

## Follow-up

| Action | Owner | Status |
|---|---|---|
| Alert when one partner exceeds 50 % rejections over an hour (≥ 5 messages) | IDO | Done 2026-10-06 |
| Interface agreement clause: 10 working days notice for format changes, test on ACC first | IDO + partner managers | In progress (PRB-002) |
| Ask each EDI partner who monitors negative notices, and when | Customer service | Open |
| Test case for format 102 kept in the regression suite | IDO | Done (`test_date_only_format_is_rejected`) |
