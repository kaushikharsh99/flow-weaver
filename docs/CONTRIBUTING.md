# FlowWeaver Contributor & Node Style Guide

Nodes are adapters. Business logic belongs in reusable modules. A node should describe *what* FlowWeaver exposes; the implementation should live in a capability package that can be reused by multiple nodes.

---

## Architectural Principles

1. **Separation of Concerns**: A node class (`node.py`) is merely an interface layer. It translates FlowWeaver's input/output ports and parameter descriptors into variables passed into pure computational functions residing in the `core/` package.
2. **The 200-Line Limit**: `node.py` files must remain small and readably clean. If `node.py` grows beyond 200 lines, extract code into the `core/` algorithm modules.
3. **No Direct Side Effects**: Nodes must never import or call OS paths (`os.path`), HTTP clients (`requests`, `urllib`), threads (`threading`), databases (`sqlite3`), or standard Python logger outputs (`logging`, `print()`) directly. All side-effect actions must go through the provided `ExecutionContext`. This ensures nodes are secure and portable across local development and cloud runner infrastructures.
4. **Reusable Capabilities**: Design plugins around *capabilities*, not singular nodes. A capability pack can expose multiple nodes (e.g. `Normalize Text`, `Tokenize Text`) that all import and share the same core algorithms inside `core/`.

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
