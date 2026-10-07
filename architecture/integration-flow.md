# Integration flow

One message from partner to database, for both channels, including the failure paths.
Design rationale: [06 · Integration design](../docs/06-integration-design.md).

```mermaid
flowchart TD
    P1[Partner REST client] -->|HTTPS + API key| GW[API gateway]
    P2[Partner EDI system] -->|AS2 / SFTP| INT[Integration layer]
    GW -->|POST /api/v1/vehicle-manifests| RX
    INT -->|POST /api/v1/edi-messages| RX

    RX[Receive<br/>log MESSAGE_RECEIVED] --> PARSE{Parse}
    PARSE -->|unreadable| SYN[Issue E-SYNTAX]
    PARSE -->|ok| MAP[Map to canonical manifest<br/>arrival → local time]
    MAP --> RULES[Content rules BR-01..06]
    RULES --> UOW
    SYN --> UOW

    UOW{{Database unit of work}}
    UOW -->|no connection / DB error| RETRY[Retry with back-off<br/>DATABASE_TIMEOUT, RETRY_n]
    RETRY -->|still failing| SPOOL[(Spool<br/>MESSAGE_PENDING · 202)]
    SPOOL -->|worker, when DB is back| RX
    RETRY -->|recovered| UOW

    UOW --> DUP{Partner + reference<br/>seen before?}
    DUP -->|yes| D[DUPLICATE · 200]
    DUP -->|no| PR[Partner rules BR-07, BR-08]
    PR --> ANY{Any issue?}
    ANY -->|yes| REJ[Store REJECTED + errors · 422 / 400]
    ANY -->|no| INS[Insert message, shipment, vehicles]
    INS -->|unique key BR-09| CONF[V-SHIPMENT-EXISTS] --> REJ
    INS -->|ok| ACC[ACCEPTED · 201]
```

## Where INC-001 happened

The path `INS → unique key BR-09` raised a database error inside the unit of work. In release
1.2.0 the connection was not returned to the pool on that error path. Five resends exhausted the
five connections; after that every message took the `RETRY → SPOOL` path.
See [INC-001](../incidents/INC-001-edi-processing-failure.md).
