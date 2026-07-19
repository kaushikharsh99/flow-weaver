# Frequently Asked Questions (FAQ)

### Q: Why does my node fail to compile due to "ModuleNotFoundError"?
A: Ensure that any third-party python packages (e.g. `polars` or `scikit-learn`) are listed in your plugin's `requirements.txt` and installed in your engine's python environment (`venv`).

---

### Q: Why does the linter throw an error about direct imports like `requests`?
A: FlowWeaver enforces a secure, sandboxed multi-threaded runtime. Standard network, database, or logging libraries bypass our logging and tracking systems. Use the provided services inside the `ExecutionContext` (e.g. standard file paths, logging methods, context telemetry) to ensure your node is portable.

---

### Q: How do I handle datasets that are larger than my system RAM?
A: Use the `StreamingDataset` or `PolarsDataset` lazy evaluation model. Streaming datasets process records in batch chunks (e.g. 10,000 rows at a time) rather than loading the entire file into memory at once, avoiding Out-Of-Memory (OOM) crashes.

---

### Q: Why is the Semantic Validator rejecting my edge connections?
A: Check that the `sourceHandle` type of the upstream output port matches the `targetHandle` type of the downstream input port. For example, you cannot connect an `audio` output port to a `tabular` input port.

---

### Q: How can I debug why my core algorithm runs slowly?
A: Run the benchmark script generated during node scaffolding:
```bash
python benchmarks/benchmark.py
```
This executes the core algorithm 1,000 times outside FlowWeaver's engine framework, logging timing profiles so you can isolate algorithmic bottlenecks.

---

### Q: What is the 200-line rule?
A: `node.py` should only act as a thin adapter config. Keep execution logic inside `core/algorithm.py` or helper utilities. If your adapter exceeds 200 lines, extract helper subroutines to external packages.
