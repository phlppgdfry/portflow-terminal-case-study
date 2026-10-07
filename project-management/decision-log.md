# Decision log

Decisions that shape the solution, with the options that were rejected and why. If someone asks
"why does it work like this?", the answer should be here.

| ID | Date | Decision | Alternatives considered | Reason | Decided by |
|---|---|---|---|---|---|
| D-001 | 2026-06-19 | One canonical model for all channels; parsers map onto it | Separate validation per channel | Business rules in one place; a new partner format is a new parser, not a new application | IDO, architecture review |
| D-002 | 2026-06-19 | Reject a manifest as a whole when any rule fails | Accept valid vehicles, reject the rest | Partial shipments create vehicles nobody knows are missing; the partner corrects once and resends | Ops manager |
| D-003 | 2026-06-24 | Idempotency on partner + message reference | Hash of the payload | The reference is under the partner's control and visible in their system; a hash breaks on a changed whitespace | IDO |
| D-004 | 2026-06-24 | Store the raw payload of every message for 90 days | Store only parsed data | Customer service and second line need to see exactly what was sent; INC-002 was diagnosed from it | IDO, ops manager |
| D-005 | 2026-07-08 | When the database is unavailable, keep the message (spool) and answer 202 | Answer 503 and let the partner retry | Partners retry differently or not at all; the terminal should not depend on that. In production: JMS queue or inbox table | IDO, IT operations |
| D-006 | 2026-07-15, confirmed 2026-10-05 | Arrival must include a time; date-only (EDI 102) is rejected | Accept date and assume 00:00 or 12:00 | An invented time puts vehicles in the wrong planning slot; a rejection is visible, a wrong time is not | Ops manager |
| D-007 | 2026-07-15 | Do not enforce the VIN check digit | Enforce position 9 | Only mandatory for North American VINs; European manufacturers often put a letter there | IDO |
| D-008 | 2026-08-05 | No replacement or cancellation messages (BGM 5 / 1) in this project | Support replace in phase 3 | Replacing requires rules for vehicles already arrived; too large for the timeline. Workaround via customer service (KI-01) | Project board |
| D-009 | 2026-10-02 | Connection pool 10, fix the leak instead of a larger pool | Keep 20; keep 5 | Measured peak 3 concurrent units of work; 10 gives headroom within the DBA's limit; a larger pool would only delay a leak, not prevent it | IDO, DBA, IT operations |
| D-010 | 2026-09-25 | Support DTM 303 (UTC offset) in the standard parser, not a Gannet-only mapping | Partner-specific mapping in the integration layer | Any future partner on UTC is then configuration only (NFR-08) | IDO |
| D-011 | 2026-06-24 | Mermaid diagrams in Markdown instead of image files | Visio / draw.io exports | Diagrams change with the text in the same review, and render on GitHub | IDO |
