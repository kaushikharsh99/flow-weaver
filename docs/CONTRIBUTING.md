# FlowWeaver Contributor & Node Style Guide

**Core Philosophy:** 
> **Nodes are adapters. Business logic belongs in reusable modules. A node should describe *what* FlowWeaver exposes; the implementation should live in a capability package that can be reused by multiple nodes.**

---

## Team Rules & Code Ownership

1. **Core framework changes require review.** Framework components (SDK, compiler, scheduler, database, API layer) are frozen and require approval from the lead maintainer before modifications.
2. **Nodes cannot modify the SDK.** Custom nodes and plugins must only import public SDK components. Do not change files inside `packages/flowweaver_sdk/`.
3. **Nodes contain adapters only; algorithms live in reusable modules.** Do not put core computational algorithms inside `node.py`. The node class is merely a wrapper exposing schema, ports, and configuration parameters to FlowWeaver.
4. **Every node must work with the `Dataset` abstraction.** Never return or pass raw pandas/polars DataFrames or lists directly between nodes. Wrap them in structured `TabularDataset`, `PolarsDataset`, `ArrowDataset`, or `StreamingDataset`.
5. **No direct filesystem or external access inside nodes.** Never use standard modules like `os.path`, `requests`, `urllib`, `threading`, or standard `logging` directly inside `node.py`. Route all I/O and telemetry actions through `ExecutionContext` to ensure node security and environment portability.
6. **No duplicate business logic across nodes.** Share common helpers and algorithms under a shared `core/` package inside your capability directory or import from utility libraries.

---

## Architectural Principles

1. **Separation of Concerns**: A node class (`node.py`) is merely an interface layer. It translates FlowWeaver's input/output ports and parameter descriptors into variables passed into pure computational functions residing in the `core/` package.
2. **The 200-Line Limit**: `node.py` files must remain small and readably clean. If `node.py` grows beyond 200 lines, extract code into the `core/` algorithm modules.
3. **Reusable Capabilities**: Design plugins around *capabilities*, not singular nodes. A capability pack can expose multiple nodes (e.g. `Normalize Text`, `Tokenize Text`) that all import and share the same core algorithms inside `core/`.

---

## Definition of Done (DoD)

A node is only complete and ready to merge when it has:
* **Working Implementation**: Core algorithm is separated from the adapter.
* **Validation**: Validates user configuration parameters before running.
* **Documentation**: Contains a `README.md` and a generated `docs.md` (using `flowweaver generate-docs`).
* **Example Pipeline**: Contains testable parameter configuration schemas in `examples/basic.json`.
* **Unit Tests**: Full coverage for the adapter, the core algorithm, and example regression verification.
* **Benchmark**: Performance metrics registered in `benchmarks/benchmark.py`.
* **Preview Support**: Support for `preview()` method to calculate subsets of dataset output for the UI.
* **Actionable Error Messages**: Friendly error explanations and recommendations when parameters or columns are missing.

---

## The Contributor Node Checklist

Every new or updated node must satisfy the following checklist during verification:

- [ ] **Metadata**: Has valid `id`, `label`, `category`, and `icon`.
- [ ] **Parameters**: Defined using `Param` descriptors with descriptive helper `labels` and `descriptions`.
- [ ] **Validation**: Parameters use min/max bounds, dropdown selections, or type guards.
- [ ] **Thin Adapter**: `node.py` is under 200 lines.
- [ ] **No Direct Side Effects**: Passes the sandboxed import constraints.
- [ ] **Return Dataset**: Port outputs are wrapped in structured `Dataset` subclasses (`TabularDataset`, etc.).
- [ ] **Uses Context**: Logs, parameters, and variable credentials route through `ExecutionContext`.
- [ ] **Documentation**: Complete description and `docs.md` generated.
- [ ] **Examples**: Includes valid configurations in `examples/basic.json`.
- [ ] **Tests**: Adapter, algorithm, and example test files pass with 100% success.
- [ ] **Benchmarks**: Core computational algorithms include performance benchmarking scripts.
- [ ] **Type Hints**: Fully typed method definitions.
