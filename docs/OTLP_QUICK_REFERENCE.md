# OTLP Logging Quick Reference

## Enable OTLP Logging

### Via Code
```python
from faciliter_lib.config import LoggerSettings
from faciliter_lib.tracing.logger import setup_logging

settings = LoggerSettings(
    log_level="DEBUG",              # Console shows DEBUG+
    otlp_enabled=True,
    otlp_endpoint="http://localhost:4318/v1/logs",
    otlp_service_name="my-app",
    otlp_log_level="INFO",          # OTLP only receives INFO+ (optional)
)
logger = setup_logging(logger_settings=settings)
```

### Via Environment
```bash
export LOG_LEVEL=DEBUG                # Console level
export OTLP_ENABLED=true
export OTLP_ENDPOINT=http://localhost:4318/v1/logs
export OTLP_SERVICE_NAME=my-app
export OTLP_LOG_LEVEL=INFO           # OTLP level (optional, defaults to LOG_LEVEL)
```

## Configuration Fields

| Field | Default | Description |
|-------|---------|-------------|
| `otlp_enabled` | `False` | Enable OTLP |
| `otlp_endpoint` | `http://localhost:4318/v1/logs` | Collector URL |
| `otlp_headers` | `{}` | Auth headers |
| `otlp_timeout` | `10` | Timeout (seconds) |
| `otlp_insecure` | `False` | Skip SSL check |
| `otlp_service_name` | `faciliter-lib` | Service name |
| `otlp_service_version` | `None` | Version tag |
| `otlp_log_level` | Inherits from `log_level` | Independent log level for OTLP handler |

## Your Collector Setup

Your `otel-collector-config.yml` already configured:
- Receives: `0.0.0.0:4318` (OTLP/HTTP)
- Exports: OpenSearch at `otel-logs` index

## Docker Compose Integration

```yaml
my-app:
  environment:
    - OTLP_ENABLED=true
    - OTLP_ENDPOINT=http://otel-collector:4318/v1/logs
    - OTLP_SERVICE_NAME=my-app
  depends_on:
    - otel-collector
```

## View Logs

**OpenSearch Dashboards:** http://localhost:5601
- Index pattern: `otel-logs*`
- Time field: `@timestamp`

**Query API:**
```bash
curl http://localhost:9200/otel-logs/_search?pretty
```

## With Authentication

```python
LoggerSettings(
    otlp_enabled=True,
    otlp_endpoint="https://collector.example.com/v1/logs",
    otlp_headers={"Authorization": "Bearer token"},
)
```

Or:
```bash
export OTLP_HEADERS='{"Authorization": "Bearer token"}'
```

## Independent Log Levels

**Use Case:** DEBUG logs on console, only INFO+ logs to OTLP (reduce costs/noise)

```python
LoggerSettings(
    log_level="DEBUG",       # Console: DEBUG, INFO, WARNING, ERROR, CRITICAL
    otlp_enabled=True,
    otlp_log_level="INFO",   # OTLP:    INFO, WARNING, ERROR, CRITICAL only
)
```

```bash
# Environment variables
export LOG_LEVEL=DEBUG
export OTLP_LOG_LEVEL=WARNING  # Only send WARNING+ to reduce OTLP ingestion
```

**Behavior:**
- `logger.debug("...")` → Console ✓, OTLP ✗
- `logger.info("...")` → Console ✓, OTLP ✓ (if OTLP_LOG_LEVEL=INFO)
- `logger.warning("...")` → Console ✓, OTLP ✓

## Multiple Handlers

```python
LoggerSettings(
    file_logging=True,      # → File
    ovh_ldp_enabled=True,   # → OVH
    otlp_enabled=True,      # → OpenTelemetry
)
```

All work simultaneously!

## Troubleshooting

**Logs not appearing?**
1. Check collector: `docker logs otel-collector`
2. Test endpoint: `curl http://localhost:4318/v1/logs`
3. Verify index: `curl http://localhost:9200/_cat/indices`

**Connection errors?**
- Verify `OTLP_ENDPOINT` is correct
- Check Docker network connectivity
- For dev: use `otlp_insecure=True`

## Full Documentation

- Architecture & setup: `docs/OTLP_LOGGING_INTEGRATION.md`
- Examples: `examples/example_otlp_logging.py`
- Implementation details: `docs/OTLP_IMPLEMENTATION_SUMMARY.md`
