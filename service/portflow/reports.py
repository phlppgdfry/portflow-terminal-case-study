"""Operational KPIs for the reporting layer (docs/11-reporting-and-kpis.md).

In the target landscape a BI tool such as WebFOCUS reads the Oracle reporting
views (V_PARTNER_QUALITY, V_DAILY_ARRIVALS). The demo computes the same
figures directly so the operations page can show them.
"""

from __future__ import annotations

import sqlite3


def kpis(conn: sqlite3.Connection) -> dict:
    since = "datetime('now', 'localtime', '-1 day')"
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute(
            f"SELECT status, COUNT(*) AS n FROM edi_message WHERE received_at >= {since} GROUP BY status"
        )
    }
    partners = [
        dict(r)
        for r in conn.execute(
            f"""SELECT partner_code AS partner,
                       COUNT(*) AS messages,
                       SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected,
                       ROUND(100.0 * SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) / COUNT(*), 1)
                           AS rejection_pct
                  FROM edi_message
                 WHERE received_at >= {since}
                 GROUP BY partner_code
                 ORDER BY rejected DESC, messages DESC"""
        )
    ]
    top_errors = [
        dict(r)
        for r in conn.execute(
            f"""SELECT e.error_code, COUNT(*) AS occurrences
                  FROM message_error e JOIN edi_message m ON m.message_id = e.message_id
                 WHERE m.received_at >= {since}
                 GROUP BY e.error_code ORDER BY occurrences DESC LIMIT 5"""
        )
    ]
    arrivals = dict(
        conn.execute(
            """SELECT COUNT(*) AS expected_today,
                      COALESCE(SUM(CASE WHEN v.status = 'ARRIVED' THEN 1 ELSE 0 END), 0) AS arrived_today
                 FROM vehicle v JOIN shipment s ON s.shipment_id = v.shipment_id
                WHERE date(s.expected_arrival) = date('now', 'localtime')"""
        ).fetchone()
    )
    latency = conn.execute(
        f"""SELECT ROUND(AVG((julianday(processed_at) - julianday(received_at)) * 86400), 2)
              FROM edi_message WHERE received_at >= {since}"""
    ).fetchone()[0]
    return {
        "messagesLast24h": by_status,
        "partners": partners,
        "topErrors": top_errors,
        "arrivals": arrivals,
        "avgProcessingSeconds": latency,
    }
