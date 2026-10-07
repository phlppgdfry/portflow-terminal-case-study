# 01 · Business context

> Fictional case. The terminal, partners, figures and incidents are invented for this portfolio.
> They are modelled on how vehicle terminals typically work, not on any specific company.

## The organisation

A multi-user **vehicle terminal in Zeebrugge** (UN/LOCODE `BEZEE`) handles new cars for import
and export: vehicles arrive by vessel, rail and truck, are parked in the yard, get technical
services, and leave again by vessel or truck. The terminal runs around the clock; the planning
and gate teams work in shifts between 06:00 and 22:00.

The **Terminal Operating System (TOS)** is the system of record for the yard: where each vehicle
is parked, which vessel or truck it leaves with, and which services it needs. The TOS can only plan
what it knows about, so it depends on **pre-advice**: the list of vehicles a logistics partner
announces before they arrive.

## The problem

Partners announce vehicles in different ways today: some by EDI, some by e-mailed spreadsheets
that the planning office retypes. Nothing checks the data when it comes in. Errors are found
at the gate, when a driver arrives with a car that is not in the system or has a VIN that does
not match.

| Observation (fictional baseline, measured over four weeks) | Value |
|---|---|
| Vehicles announced per day, all partners | ~2,500 |
| Manifests containing at least one error | ~4 % |
| Gate exceptions caused by missing or wrong pre-advice | ~60 per day |
| Average time to resolve one gate exception (phone calls, e-mails, manual entry) | ~12 minutes |
| Time lost per day across gate and planning | **~12 hours** |

What the operations manager said in the intake interview:

> "We find out at the gate that the data was wrong. By then the truck is waiting, the yard plan
> is already made, and we are on the phone with a partner who sent the file six hours ago."

## The opportunity

Check the data **when it arrives**, not when the vehicle does:

- reject a bad manifest within seconds and tell the partner exactly what is wrong;
- show operations which announcements were rejected, so nobody plans on wrong data;
- make onboarding a new logistics partner a repeatable procedure instead of a project.

## Scope of this case

| In scope | Out of scope (later phases) |
|---|---|
| Inbound vehicle manifests over REST (JSON) and EDI | Outbound messages to partners (status, departure) |
| Validation, rejection with reasons, operations view | Changes inside the TOS itself |
| Duplicate detection and safe handling of database outages | Replacement / cancellation messages (BGM function 5 and 1) |
| Gate arrival registration (to measure expected vs arrived) | Billing, customs, damage inspection |
| Onboarding a new partner (CR-001) | Mobile apps for drivers |
| Operational support: monitoring, incidents, changes, releases | |

## Who is involved

The full list with interest and influence is in the
[stakeholder matrix](../project-management/stakeholder-matrix.md). In short: the **operations
manager** owns the problem, the **gate and planning teams** use the result, **external partners**
change how they send data, **IT operations, the DBA and the integration team** run the platform,
and the **IT manager** sponsors the project.

## Where this leads

The business need is turned into requirements in
[02 · Business requirements](02-business-requirements.md).
