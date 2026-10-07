-- Session checks for INC-001-type problems (connection pool exhaustion).
-- Needs access to the V$ views (SELECT_CATALOG_ROLE or a DBA), so in practice
-- second-line support runs these together with the DBA.

SET PAGESIZE 100
SET LINESIZE 200
COLUMN username FORMAT A12
COLUMN machine FORMAT A24
COLUMN program FORMAT A28
COLUMN resource_name FORMAT A12

PROMPT D1 Sessions of the application schema, per client machine and state
SELECT username, machine, program, status, COUNT(*) AS sessions
  FROM v$session
 WHERE username = 'PORTFLOW'
 GROUP BY username, machine, program, status
 ORDER BY sessions DESC;

PROMPT D2 Application sessions idle for more than 5 minutes while holding an open transaction
PROMPT    (a leaked pooled connection typically looks like this)
SELECT s.sid, s.serial#, s.machine, s.status, s.last_call_et AS idle_seconds, t.start_time
  FROM v$session s
  JOIN v$transaction t ON t.addr = s.taddr
 WHERE s.username = 'PORTFLOW'
   AND s.status = 'INACTIVE'
   AND s.last_call_et > 300;

PROMPT D3 Session and process limits of the instance
SELECT resource_name, current_utilization, max_utilization, limit_value
  FROM v$resource_limit
 WHERE resource_name IN ('sessions', 'processes');
