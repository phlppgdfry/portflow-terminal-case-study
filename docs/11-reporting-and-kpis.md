# 11 · Reporting and KPIs

Operational data becomes business information in three steps:

```
Operational tables (EDI_MESSAGE, SHIPMENT, VEHICLE, ...)
        ↓  reporting views, owned by the application (V_PARTNER_QUALITY, V_DAILY_ARRIVALS)
Reporting layer (WebFOCUS-type BI, read-only account)
        ↓
Reports and dashboards for operations, management and partner reviews
```

The BI tool reads **views**, never the base tables. The application can then change its tables
without breaking reports, as long as the views keep their columns. That is a contract, just like
the API.

## KPIs

| KPI | Definition | Source | Audience | Target |
|---|---|---|---|---|
| Vehicles announced | Vehicles in accepted manifests, per day and partner | `V_DAILY_ARRIVALS.vehicles_expected` | Operations | Trend |
| Arrived vs expected | `vehicles_arrived / vehicles_expected` per arrival day | `V_DAILY_ARRIVALS` | Planning | > 95 % by end of day |
| Rejection rate | Rejected / all messages, per partner per day | `V_PARTNER_QUALITY.rejection_pct` | Operations manager, partner reviews | < 2 % |
| Top rejection reasons | Count per error code | `MESSAGE_ERROR` (Q2) | Customer service, partners | — |
| Processing time | Average seconds between receipt and outcome | `V_PARTNER_QUALITY.avg_processing_s` | IT | < 2 s (NFR-02) |
| Pending backlog | Messages waiting in the spool | `/health` | IT | 0 |
| Gate exceptions from pre-advice | Counted in the TOS | TOS report | Operations manager | < 15 / day (business case) |

The last KPI is the one the project is judged on; the others explain why it moves.

## Example: weekly partner quality report

| Partner | Messages | Rejected | Rejection % | Main reason | Trend |
|---|---|---|---|---|---|
| OSP | 212 | 3 | 1.4 % | `V-VIN-FORMAT` | ↓ |
| HRN | 168 | 22 | 13.1 % | `V-ARRIVAL-DATE` (INC-002, Monday) | ↑ one-off |
| GNT | — | — | — | onboarding | — |

This report is the agenda for the monthly call with each partner: a number, a reason, an action.

## In the demo

`GET /api/v1/reports/kpis` returns the same figures for the last 24 hours, computed in
[`reports.py`](../service/portflow/reports.py); the operations page shows them as tiles. The
Oracle views are created by [schema.sql](../database/schema.sql) and queried by Q10 in
[diagnostic-queries.sql](../database/diagnostic-queries.sql), which CI runs on a real Oracle database.

## WebFOCUS in practice

- A WebFOCUS report or dashboard is built on a **synonym** (metadata) over the view.
- Reports run on demand or are scheduled (ReportCaster) and mailed, for example the partner
  quality report every Monday 07:00.
- Access is controlled per report group: partners never see each other's figures.

## Oracle APEX as an alternative operations screen

The `/ops` page could equally be a small APEX application on the same schema: an interactive
report on `EDI_MESSAGE` filtered on `REJECTED`, a detail page with `MESSAGE_ERROR` rows and the
raw payload, and authorisation through the existing directory. For internal screens on Oracle
data that is often faster to build and easier to hand over than a custom web application.
The trade-off: logic must stay in the service (validation), not drift into APEX page processes.
