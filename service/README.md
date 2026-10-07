# PortFlow service

The reference implementation behind the [technical specification](../docs/04-technical-specification.md).
Python 3.12+, standard library only: nothing to install.

```bash
python3 -m portflow serve                 # http://127.0.0.1:8080/ops
python3 -m unittest discover -s tests -v
python3 -m portflow set-partner-status GNT ACTIVE
```

| Module | Responsibility |
|---|---|
| [`edi.py`](portflow/edi.py) | EDIFACT tokenizer (UNA, release character) and VMANIF → canonical mapping with envelope checks |
| [`mapping.py`](portflow/mapping.py) | JSON → canonical mapping; date formats and conversion to terminal local time |
| [`model.py`](portflow/model.py) | Canonical manifest, vehicle, issue |
| [`validation.py`](portflow/validation.py) | Business rules BR-01 to BR-06 |
| [`service.py`](portflow/service.py) | Processing: validate, unit of work, retry, spool, partner rules |
| [`db.py`](portflow/db.py) | Bounded connection pool and queries |
| [`reports.py`](portflow/reports.py) | KPIs |
| [`server.py`](portflow/server.py) | HTTP API, health, operations page, spool worker |

Configuration is by environment variable; see the table in the
[technical specification](../docs/04-technical-specification.md#5-configuration).

Tests are named after the acceptance tests they automate (`test_at01_…` to `test_at15_…`), and
they read the sample files in [`integrations/`](../integrations/), so the specification's
examples are always valid.
