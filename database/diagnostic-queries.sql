-- Diagnostic queries for second-line support (Oracle).
-- Each query names the runbook step that uses it (docs/09-operational-runbook.md).
-- Read-only: safe to run on production with the application read-only account.

SET PAGESIZE 100
SET LINESIZE 200
SET VERIFY OFF
ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI';
ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS';
COLUMN partner_code FORMAT A8
COLUMN partner_id FORMAT A8
COLUMN error_code FORMAT A20
COLUMN shipment_ref FORMAT A16
COLUMN message_ref FORMAT A14
COLUMN vin FORMAT A17
COLUMN name FORMAT A26
COLUMN shipments FORMAT A60
COLUMN processing_time FORMAT A28

PROMPT Q1 Rejected messages per partner, last 24 hours (runbook R2)
SELECT partner_code,
       COUNT(*) AS rejected_messages
  FROM edi_message
 WHERE status = 'REJECTED'
   AND received_at > SYSTIMESTAMP - INTERVAL '24' HOUR
 GROUP BY partner_code
 ORDER BY rejected_messages DESC;

PROMPT Q2 Most frequent rejection reasons per partner, last 24 hours (runbook R2)
SELECT m.partner_code,
       e.error_code,
       COUNT(*) AS occurrences,
       MAX(m.received_at) AS last_seen
  FROM message_error e
  JOIN edi_message m ON m.message_id = e.message_id
 WHERE m.received_at > SYSTIMESTAMP - INTERVAL '24' HOUR
 GROUP BY m.partner_code, e.error_code
 ORDER BY occurrences DESC, last_seen DESC;

PROMPT Q3 Message flow per 15 minutes, last 6 hours: a gap means the flow stopped (runbook R1, INC-001)
SELECT TRUNC(received_at, 'HH24')
         + NUMTODSINTERVAL(FLOOR(EXTRACT(MINUTE FROM received_at) / 15) * 15, 'MINUTE') AS bucket_start,
       COUNT(*) AS messages,
       SUM(CASE WHEN status = 'ACCEPTED' THEN 1 ELSE 0 END) AS accepted
  FROM edi_message
 WHERE received_at > SYSTIMESTAMP - INTERVAL '6' HOUR
 GROUP BY TRUNC(received_at, 'HH24')
         + NUMTODSINTERVAL(FLOOR(EXTRACT(MINUTE FROM received_at) / 15) * 15, 'MINUTE')
 ORDER BY bucket_start;

PROMPT Q4 Heartbeat: messages stored in the last 10 minutes (zero during business hours = alert)
SELECT COUNT(*) AS messages_last_10_min
  FROM edi_message
 WHERE received_at > SYSTIMESTAMP - INTERVAL '10' MINUTE;

PROMPT Q5 Silent partners: active partners without any message in the last 6 hours (runbook R1)
SELECT p.partner_id,
       p.name,
       MAX(m.received_at) AS last_message
  FROM partner p
  LEFT JOIN edi_message m ON m.partner_code = p.partner_id
 WHERE p.status = 'ACTIVE'
 GROUP BY p.partner_id, p.name
HAVING MAX(m.received_at) IS NULL
    OR MAX(m.received_at) < SYSTIMESTAMP - INTERVAL '6' HOUR;

PROMPT Q6 Slow processing: messages that took more than 5 seconds (runbook R3)
SELECT message_id,
       partner_code,
       message_ref,
       received_at,
       processed_at - received_at AS processing_time
  FROM edi_message
 WHERE processed_at - received_at > INTERVAL '5' SECOND
   AND received_at > SYSTIMESTAMP - INTERVAL '24' HOUR
 ORDER BY received_at DESC;

PROMPT Q7 Overdue vehicles: expected more than 2 hours ago and not arrived (operations question)
SELECT s.partner_id,
       s.shipment_ref,
       s.expected_arrival,
       COUNT(*) AS vehicles_open
  FROM shipment s
  JOIN vehicle v ON v.shipment_id = s.shipment_id
 WHERE v.status = 'EXPECTED'
   AND s.expected_arrival < SYSTIMESTAMP - INTERVAL '2' HOUR
 GROUP BY s.partner_id, s.shipment_ref, s.expected_arrival
 ORDER BY s.expected_arrival;

PROMPT Q8 Data quality: VIN expected on more than one open shipment
SELECT v.vin,
       COUNT(*) AS open_shipments,
       LISTAGG(s.partner_id || '/' || s.shipment_ref, ', ') WITHIN GROUP (ORDER BY s.expected_arrival) AS shipments
  FROM vehicle v
  JOIN shipment s ON s.shipment_id = v.shipment_id
 WHERE v.status = 'EXPECTED'
 GROUP BY v.vin
HAVING COUNT(*) > 1;

PROMPT Q9 Full history of one VIN (user asks: where is my car?)
DEFINE vin = 'WVWZZZE1ZPP012345'
SELECT 'ANNOUNCED' AS step, m.received_at AS at_time, s.partner_id AS detail_1, s.shipment_ref AS detail_2
  FROM vehicle v
  JOIN shipment s ON s.shipment_id = v.shipment_id
  JOIN edi_message m ON m.message_id = s.message_id
 WHERE v.vin = '&vin'
UNION ALL
SELECT e.event_type, e.event_time, e.source, NULL
  FROM terminal_event e
 WHERE e.vin = '&vin'
 ORDER BY at_time;
UNDEFINE vin

PROMPT Q10 Reporting views used by the BI layer
SELECT * FROM v_partner_quality WHERE report_day >= TRUNC(SYSDATE) - 1 ORDER BY report_day, partner_code;
SELECT * FROM v_daily_arrivals WHERE arrival_day >= TRUNC(SYSDATE) ORDER BY arrival_day, partner_id;
