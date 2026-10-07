# 10 · Infrastructure and application server

Where PortFlow would run in a classic enterprise terminal landscape, and what application
management needs to know about each layer.

> **Scope.** This page does not claim production experience with IBM Power, AIX, JBoss EAP,
> iWay or WebFOCUS. It shows how the pieces fit together, which settings matter for an
> application like this one, and what to check first. The concepts (pools, deployments, logs,
> sessions) are the same ones the demo implements and the incidents exercise.

## The stack

```
IBM Power server (POWER processors, firmware, HMC)
        ↓  PowerVM: logical partitions (LPARs), VIOS for shared I/O
AIX (the IBM Unix)
        ↓
Java runtime (IBM Semeru / IBM SDK on AIX)
        ↓
JBoss EAP application server (standalone or domain mode)
        ↓  deployment
portflow.war  ── datasource java:/jdbc/PortFlowDS ──►  Oracle Database (often on its own LPAR)
```

| Layer | What it is | Who usually owns it | What the IDO needs from it |
|---|---|---|---|
| IBM Power (formerly pSeries / System p) | IBM's server line, built for long uptime; partitioned into LPARs | Infrastructure / Unix team | Capacity, maintenance windows |
| AIX | IBM's Unix for Power | Unix team | Disk space, processes, OS errors, scheduled jobs |
| JBoss EAP | Red Hat's Jakarta EE application server (WildFly is the community version) | Middleware team | Deploy / undeploy, datasources, logs, JVM memory |
| Oracle Database | Relational database | DBA | Schema changes via release, sessions, performance, backups |
| iWay | Integration server from the same vendor family as WebFOCUS; EDI adapters, routing, transformation | Integration team | Routes per partner, EDI transport, error queues |
| WebFOCUS | BI and reporting platform | BI team | Reports on the reporting views |
| Oracle APEX | Low-code web applications inside the Oracle database | DBA / developers | Quick internal screens on Oracle data |

iWay and WebFOCUS both come from Information Builders (now part of the TIBCO / Cloud Software
Group portfolio), which is why they are often found together: one moves the data, the other
reports on it.

## JBoss EAP: what matters for PortFlow

**Deployment.** The application is one WAR. JBoss deploys it through the CLI or the deployment
scanner.

```bash
jboss-cli.sh --connect --command="deploy /opt/releases/portflow-1.3.0.war --force"
jboss-cli.sh --connect --command="deployment-info --name=portflow.war"
jboss-cli.sh --connect --command="undeploy portflow.war"
```

Keep the previous WAR on disk until the release is closed; that is the rollback.

**Datasource.** The connection pool lives in the application server, not in the application.
These attributes decide whether INC-001 can happen and how fast it shows:

| Attribute | PortFlow value | Why |
|---|---|---|
| `min-pool-size` | 2 | Warm connections for the first messages after a quiet night |
| `max-pool-size` | 10 | NFR-09, agreed with the DBA after PRB-001 |
| `blocking-timeout-wait-millis` | 2000 | Same as `PORTFLOW_POOL_TIMEOUT`: fail fast, retry, spool |
| `background-validation` / `validate-on-match` | background, 60 s | Detect connections the database or a firewall has closed |
| `statistics-enabled` | true | Needed to see pool usage in monitoring |

Pool usage, the first thing to check in a "messages not processed" incident:

```bash
jboss-cli.sh --connect --command="/subsystem=datasources/data-source=PortFlowDS/statistics=pool:read-resource(include-runtime=true)"
# ActiveCount, AvailableCount, InUseCount, MaxUsedCount, TimedOut, WaitCount
```

`InUseCount` at the maximum while the database is idle is the INC-001 pattern. A flush releases
them without a restart: `:flush-all-connection-in-pool`. Leak detection (the `cached-connection-manager`
debug option) can log where a connection was borrowed and never returned; useful on ACC, too
noisy for production.

**Logs.** `standalone/log/server.log` (or the path the middleware team configured). PortFlow's
events are single lines with a fixed event name, so `grep DATABASE_TIMEOUT server.log` works.

## AIX: first checks on the host

| Question | Command |
|---|---|
| Which AIX level? | `oslevel -s` |
| CPU and memory now | `topas`, `vmstat 5 5` |
| Disk full? (spool and logs live on disk) | `df -g` |
| Paging space | `lsps -a` |
| Hardware or OS errors | `errpt` (summary), `errpt -a` (detail) |
| Is the Java process running, with which arguments? | `ps -ef | grep java` |
| Who listens on the HTTP port? | `netstat -an | grep 8080` |

Most changes on the host itself go through the Unix team; the application owner reads and
reports, and changes things under the application's own user only.

## Oracle: the application owner's share

- Schema changes only through a reviewed script in a release ([schema.sql](../database/schema.sql)).
- Support works with read-only queries ([diagnostic-queries.sql](../database/diagnostic-queries.sql)).
- Session problems are investigated together with the DBA ([dba-session-checks.sql](../database/dba-session-checks.sql)).
- Connection test: `tnsping PORTFLOWDB`, then `sqlplus portflow_ro@PORTFLOWDB` and `SELECT 1 FROM dual`.

## Mapping the demo to this stack

| Demo | Production equivalent |
|---|---|
| `python -m portflow serve` | WAR deployed on JBoss EAP |
| `PORTFLOW_POOL_SIZE`, `PORTFLOW_POOL_TIMEOUT` | Datasource `max-pool-size`, `blocking-timeout-wait-millis` |
| `/health` → `pool.available` | Datasource statistics `AvailableCount` |
| `spool/` directory | JMS queue in JBoss, or an inbox table in Oracle |
| SQLite file | Oracle schema `PORTFLOW` |
| `scripts/smoke-test.sh` | Same script, pointed at the production URL |
