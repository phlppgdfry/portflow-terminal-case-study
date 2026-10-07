# System context

PortFlow and everything it talks to. Explanation per component:
[05 · Architecture](../docs/05-architecture.md).

```mermaid
flowchart TB
    classDef ext fill:#eef3fb,stroke:#1f5fae,color:#17202a
    classDef sys fill:#e9f6ef,stroke:#1e7f4f,color:#17202a
    classDef user fill:#fdf3e4,stroke:#a15c00,color:#17202a

    OSP["Osprey Vehicle Logistics<br/>sends manifests over REST"]:::ext
    HRN["Heron Shipping Lines<br/>sends EDI"]:::ext
    GNT["Gannet Auto Carriers<br/>EDI, onboarding (CR-001)"]:::ext

    PF["PortFlow<br/>validates manifests, shows outcomes"]:::sys
    TOS["Terminal Operating System<br/>plans the yard"]:::sys
    BI["Reporting (BI)"]:::sys

    PLAN["Planners"]:::user
    GATE["Gate clerks"]:::user
    CS["Customer service"]:::user
    SUP["Second-line support"]:::user

    OSP -- "manifest (JSON)" --> PF
    HRN -- "manifest (VMANIF)" --> PF
    GNT -- "manifest (VMANIF)" --> PF
    PF -. "pre-advice (phase 3)" .-> TOS
    PF -- "KPIs via views" --> BI
    PLAN -- "expected shipments" --> PF
    GATE -- "arrival by VIN" --> PF
    CS -- "why was it rejected?" --> PF
    SUP -- "health, logs, queries" --> PF
```

| Actor / system | Relationship |
|---|---|
| Logistics partners | Announce vehicles; receive accept / reject feedback |
| Planners | See which shipments are expected and complete |
| Gate clerks | Register arrivals |
| Customer service | Explain rejections to partners |
| Second-line support | Monitor and troubleshoot |
| TOS | Will receive accepted pre-advice (IF-04, phase 3) |
| BI | Reads reporting views |
