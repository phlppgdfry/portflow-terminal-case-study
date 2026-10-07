# 12 · Partner onboarding

The repeatable procedure for connecting a new logistics partner. The worked example is Gannet
Auto Carriers in [CR-001](../changes/CR-001-new-logistics-partner.md).

```
Request → Intake → Interface agreement → Mapping review → Security & access
       → Configuration on ACC → Partner tests → UAT → Change & release → Hypercare → Support
```

## Steps and checklist

| # | Step | Output | Owner | Typical duration |
|---|---|---|---|---|
| 1 | **Request** from commercial / operations: which partner, volumes, start date | Onboarding request | Operations manager | — |
| 2 | **Intake call** with the partner's IT contact: channel (REST or EDI), transport, test capacity, contacts | Intake notes; partner register entry with status `ONBOARDING` | IT Development Officer | 1 week |
| 3 | **Interface agreement**: send the [mapping specification](../integrations/mapping-specification.md) and [error scenarios](../integrations/error-scenarios.md); agree message version, reference format, time zone, volumes, retry behaviour | Signed interface agreement | IDO + partner | 1 week |
| 4 | **Mapping review**: the partner sends 3 real (anonymised) files; compare field by field against the spec | Gap list. No gaps → configuration only. Gaps → change in the parser (as for GNT: UTC times) | IDO | 2 days |
| 5 | **Security and access**: API key or AS2 certificate / SFTP account; firewall rule; check that the sender id is bound to the partner | Credentials on ACC | Security officer, integration team | 1 week (lead time!) |
| 6 | **Configuration on ACC**: partner row, channel, integration route | Partner can send to ACC | IDO, integration team | 1 day |
| 7 | **Partner tests**: the partner sends the agreed test set (valid, invalid, duplicate, large) | Test report | Partner, IDO | 1 week |
| 8 | **UAT**: operations checks the shipments look right in their screens | UAT sign-off | Operations | 2 days |
| 9 | **Change and release**: CR to the CAB, release plan, go-live date with the partner | Approved CR | IDO | per CAB cycle |
| 10 | **Go-live**: activate partner (`ACTIVE`) in the release window | Partner live | IT operations, DBA | window |
| 11 | **Hypercare**: daily KPI check and call with the partner in week 1 | Hypercare log | IDO | 1 week |
| 12 | **Hand-over to support**: partner in the register, contacts on file, known issues listed | Runbook updated | IDO | — |

## Partner test set (minimum)

| Case | File | Expected |
|---|---|---|
| P1 | Valid manifest, 2 to 10 vehicles | Accepted |
| P2 | Same file again | Duplicate |
| P3 | Same shipment, new message reference | Rejected `V-SHIPMENT-EXISTS` |
| P4 | One VIN with letter O | Rejected `V-VIN-FORMAT` |
| P5 | Wrong terminal code | Rejected `V-TERMINAL` |
| P6 | Truncated file (cut halfway) | Rejected `E-SYNTAX` |
| P7 | Largest realistic manifest (e.g. full vessel deck, 600 vehicles) | Accepted within 2 s |
| P8 | A manifest sent around a daylight saving change, if the partner sends UTC | Local time correct |

## Lessons built into the procedure

- **Security lead time is the critical path.** Certificates and firewall rules take longer than
  mapping work; request them in step 2, not step 5.
- **Agree how the partner announces its own changes** ([PRB-002](../incidents/problem-analysis.md#prb-002-partner-changes-reach-us-as-incidents)):
  the interface agreement now includes a 10 working day notice for format changes and a test slot on ACC.
- **Ask for real files early.** The UTC difference for Gannet showed up in step 4 from one sample
  file; in a document it would have been missed.
