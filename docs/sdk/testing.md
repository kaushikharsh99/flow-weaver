# FlowWeaver Node Testing Guide

High quality testing keeps capability packages easy to maintain. In FlowWeaver, tests are segmented into three categories to isolate visual integration concerns from computational logic.

---

## The Three Test Layers

When a node capability package is scaffolded, three tests are generated inside the `tests/` directory:

### 1. Adapter Interface Tests (`test_node.py`)
Verifies that the Node class adapts correctly to FlowWeaver.
- Tests that ports (`inputs`/`outputs`) are declared with the right types.
- Tests that parameters match expected descriptors.
- Emulates running the node with a mock execution context.

```python
from node import NormalizeTextNode

def test_node_definition():
    node = NormalizeTextNode()
    assert node.category == "Text"
    assert len(node.inputs) == 1
    assert node.inputs[0].type == "text"
```

### 2. Core Algorithm Tests (`test_algorithm.py`)
Verifies pure-python business logic independent of any FlowWeaver imports.
- Feed direct input variables/dataframes to your algorithms.
- Test edge cases, speed, performance, and exceptions.

```python
from core.algorithm import process_data

def test_process_data_empty():
    res = process_data("")
    assert res == ""
```

### 3. Example Schema Tests (`test_examples.py`)
Verifies that example parameter JSON configurations saved in `examples/` match the node schema and execute successfully.

---

## Executing Tests via CLI

Run all tests on a node capability directory using the developer assistant CLI:

```bash
flowweaver test-node ./plugins/category/my_plugin
```
This imports your node, parses parameter schema entries from `examples/basic.json`, verifies constraints, executes the adapter run, and logs output diagnostics.
