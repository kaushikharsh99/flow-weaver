# Creating Custom Nodes

In FlowWeaver, a node is merely a visual **adapter** that wraps and configures a reusable computational block. Core logic and heavy business code should reside outside the adapter inside generic Python modules.

---

## Enforcing the "Node as Adapter" Pattern

To keep the codebase maintainable, FlowWeaver enforces two strict lint constraints:
1. **The 200-Line Limit**: `node.py` (the adapter file) must remain under 200 lines. If logic expands, extract it to a module inside `core/`.
2. **Prohibited Imports**: `node.py` must never import `requests`, `threading`, `sqlite3`, `logging`, or `os.path` directly. All actions must be routed via `ExecutionContext`.

```
Visual Workspace
       ↓
    node.py         ← (Exposes ports and parameters, under 200 lines)
       ↓
   service.py       ← (Optional coordinator orchestration layer)
       ↓
 core/algorithm.py  ← (Pure Python algorithm, zero FlowWeaver dependencies)
```

---

## Step 1: Scaffold a Node via CLI

Use the developer assistant CLI to generate the modular capability directory structure inside the `plugins/` directory:

```bash
flowweaver create-node CleanText --category Transform
```

### Generated Structure:
- `node.py`: Exposes ports and parameters.
- `service.py`: Orchestrator coordinating core logic.
- `core/algorithm.py`: Reusable computational Python logic.
- `utils/helpers.py`: Auxiliary context helpers.
- `tests/`: Adapter, algorithm, and example test files.
- `examples/`: Config mock files (`basic.json`).
- `data/`: Sample CSV/JSON datasets.
- `benchmarks/`: Script to measure processing loop speeds.

---

## Step 2: Implement Core Logic

Put your pure data processing code inside `core/algorithm.py`:

```python
# core/algorithm.py
def process_data(dataset, replacement_char=" ", ctx=None):
    if ctx:
        ctx.log("Replacing space tabs inside core...")
    rows = dataset.to_list()
    for r in rows:
        r["text"] = str(r["text"]).replace("\t", replacement_char)
    return TabularDataset(rows, columns=dataset.columns())
```

---

## Step 3: Configure Node Adapter

Wrap the logic by declaring ports and parameter constraints inside `node.py`:

```python
# node.py
from flowweaver.sdk import Node, Input, Output, Param, node
from service import CleantextService

@node(name="Clean Text", category="Transform")
class CleantextNode(Node):
    in_data = Input.tabular()
    out = Output.tabular()
    
    char = Param.text(label="Replacement Space", default=" ")

    def execute(self, inputs, ctx):
        service = CleantextService()
        return {"out": service.run(inputs.get("in_data"), ctx.parameters.get("char"), ctx)}
```
---

## Step 4: Validate and Package

Verify constraints and build the tarball archive:
```bash
flowweaver lint-node ./CleanText
flowweaver package-plugin ./CleanText
```
