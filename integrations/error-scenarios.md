# Error scenarios

Every outcome other than ACCEPTED, what causes it, and who does what. Partners receive this table
during onboarding; customer service uses it to explain rejections.

## Business rule rejections (HTTP 422, stored as REJECTED)

| Code | Rule | Typical cause | Partner action |
|---|---|---|---|
| `V-REQUIRED` | BR-01 | Mandatory field empty or missing (also a vehicle without VIN) | Fill the field named in `field` |
| `V-VIN-FORMAT` | BR-02 | VIN not 17 characters, lower case, or contains I, O or Q (often O instead of 0) | Correct the VIN |
| `V-VIN-DUPLICATE` | BR-03 | Same VIN twice in one manifest | Remove the duplicate line |
| `V-TERMINAL` | BR-04 | Manifest meant for another terminal | Send to the right terminal |
| `V-ARRIVAL-DATE` | BR-05 | Not ISO 8601, no time of day, EDI format 102, or `+` not released in format 303 | Send date and time in an accepted format |
| `V-NO-VEHICLES` / `V-TOO-MANY` | BR-06 | Empty manifest, or more than 1,000 vehicles | Split into several shipments |
| `V-PARTNER-UNKNOWN` | BR-07 | Partner code not registered | Contact the terminal's IT; check the code |
| `V-PARTNER-INACTIVE` | BR-07 | Partner still onboarding, or suspended | Wait for go-live / contact the terminal |
| `V-PARTNER-CHANNEL` | BR-08 | REST partner sending EDI or the other way round | Use the agreed channel |
| `V-SHIPMENT-EXISTS` | BR-09 | Shipment reference already announced (often a resend with a new message reference) | Do nothing if it is a resend; otherwise use a new shipment reference |
| `V-FUNCTION` | D-008 | EDI `BGM` function other than 9 (e.g. 5 = replace) | Send a new shipment; ask customer service to cancel the old one |

All rule failures are returned together, so one correction round is enough.

## Technical outcomes

| Outcome | HTTP | Cause | Partner action | Terminal action |
|---|---|---|---|---|
| `E-SYNTAX` (REJECTED) | 400 | Invalid JSON; EDI envelope broken, truncated or wrong segment count | Fix the format; check the file was sent completely | If one partner suddenly gets many: R2 in the runbook |
| DUPLICATE | 200 | Same partner + message reference seen before | None | None |
| PENDING | 202 | Database unavailable after retries; message kept in the spool | None, and **do not** resend under a new reference | R1 in the runbook; backlog drains automatically |
| 413 | 413 | Body larger than 1 MB | Split the manifest | — |
| 503 on read endpoints | 503 | No database connection for the operations page | — | R1 |

## Scenarios as tested

| Scenario | Input | Expected | Test |
|---|---|---|---|
| Valid manifest | sample JSON | ACCEPTED | AT-01 |
| Missing VIN | vehicle without `vin` | REJECTED `V-REQUIRED` | AT-03 |
| Unknown partner | `partnerId: XYZ` | REJECTED `V-PARTNER-UNKNOWN` | AT-04 |
| Duplicate message | same message twice | DUPLICATE | AT-05 |
| Database unavailable | all connections busy | PENDING, later ACCEPTED | AT-07 |
| Invalid JSON | `{not json` | REJECTED `E-SYNTAX`, HTTP 400 | AT-08 |
| Truncated EDI | file cut before last `'` | REJECTED `E-SYNTAX` | `test_truncated_interchange_is_a_syntax_error` |
| Wrong segment count | `UNT+18` for 19 segments | REJECTED `E-SYNTAX` | `test_wrong_segment_count_is_a_syntax_error` |
