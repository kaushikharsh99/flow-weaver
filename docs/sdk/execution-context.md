# FlowWeaver Execution Context Guide

The `ExecutionContext` provides nodes with state, configuration, and helper services. Because nodes run sandboxed within multi-threaded execution environments, they must **never** perform direct side-effects using standard modules (such as `os`, `requests`, `threading`, or standard `logging`).

Every operation must be routed through `ExecutionContext`.

---

## Accessing Configuration & State

### 1. `ctx.parameters`
Contains the key-value dictionary of node-specific settings configured by the user in the Inspector:
```python
threshold = ctx.parameters.get("threshold", 0.85)
```

### 2. `ctx.variables`
Enables accessing pipeline-level runtime variables (e.g. env vars, date stamps, runtime credentials):
```python
api_key = ctx.variables.get("API_KEY")
```

---

## Log Routing via Context

Standard `print()` or `logging.getLogger()` logs to standard output, bypasses the execution runner, and won't show up in the web client's debugger log stream.

Always use the context logger:

```python
# GOOD: Context-aware logging. Show up in UI and database run records.
ctx.log("Fetched 50 rows from source database.")
ctx.log("Validation failed for cell value.", level="warn")
ctx.log("Core algorithm completed.", level="debug")

# BAD: UI won't capture these
print("Processing data...")
import logging
logging.info("Core algorithm completed.")
```

---

## Profiling and Metrics Reporting

You can report custom execution metrics that are aggregated by the profiler:

```python
# Report custom telemetry metrics
ctx.metrics.increment("rows_processed", count=100)
ctx.metrics.gauge("ram_usage_mb", 45.2)

# Throughput calculation
start_time = ctx.metrics.start_timer()
# computational task...
ctx.metrics.stop_timer(start_time, name="hashing_duration")
```

---

## State & Cancellation Management

Long-running nodes should check the context state periodically to support safe pipeline execution cancellation:

```python
for chunk in large_dataset:
    # Check if user clicked "Cancel" in the UI
    if ctx.is_cancelled():
        ctx.log("Cancellation detected, cleaning up resources...")
        break
    process(chunk)
```

---

## Why Enforce Context Routing?
- **Portability**: Running on local workers, distributed Celery nodes, or serverless functions requires abstracting system paths.
- **Monitoring**: Centralized logs, error alerts, and progress percentages rely on context hook points.
- **Security**: Ensures nodes operate within declared sandboxed limits.
