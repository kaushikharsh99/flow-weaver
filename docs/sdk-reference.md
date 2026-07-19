# FlowWeaver Python SDK Reference

The `flowweaver.sdk` provides the classes and decorators to build capability nodes.

---

## 1. Node Class decorator (`@node`)

Configures metadata on a custom node:

```python
from flowweaver.sdk import node, Node

@node(
    name="Clean Spacing",
    category="Transform",
    icon="Wand2",
    description="Clean punctuation formatting.",
    version="1.0.0",
    tags=["clean", "formatting"]
)
class CleanSpacingNode(Node):
    ...
```

### Decorator Options:
* `name` (str): Label displayed in the visual palette.
* `category` (str): Palette category (`Loaders`, `Filters`, `Transform`, `Dedup`, `NLP`, `Export`).
* `icon` (str): Lucide React icon name.
* `description` (str): Sub-label. Autodetects class docstring if omitted.
* `version` (str): Version tag (defaults to `1.0.0`).

---

## 2. Port Descriptors

Declared as class-level attributes, ports are parsed by the metaclass:
- `Input.tabular(label, required=True)`
- `Input.text(label, required=True)`
- `Input.any(label, required=True)`
- `Output.tabular(label)`
- `Output.text(label)`
- `Output.any(label)`

---

## 3. Parameter Descriptors (`Param`)

Parameters define visual UI fields inside the frontend Inspector panel:
* `Param.text(label, default, placeholder)`
* `Param.textarea(label, default, rows)`
* `Param.number(label, default, min, max, step)`
* `Param.slider(label, default, min, max, step)`
* `Param.boolean(label, default)`
* `Param.select(label, default, options)`
* `Param.color(label, default)`
* `Param.file(label, default, accept)`
* `Param.regex(label, default)`
* `Param.column(label, default)`
* `Param.secret(label)`
* `Param.json(label, default)`
* `Param.expression(label, default)`

---

## 4. Execution Context (`ExecutionContext`)

Provides log routing, variables, and cancellation listeners:
- `ctx.parameters`: Dictionary of inspector configurations.
- `ctx.variables`: Dictionary of pipeline-level env variables.
- `ctx.log(msg)` / `ctx.log_warn(msg)` / `ctx.log_error(msg)`: Log messages displayed in the web app log stream.
- `ctx.report_progress(percent, msg=None)`: Reports step progress (0-100) dynamically.
- `ctx.is_cancelled() -> bool`: Returns `True` if execution is aborted.
- `ctx.add_artifact(Artifact)`: Registers an output file.

---

## 5. Dataset API

- `TabularDataset(data: List[Dict], columns: List[str])`: Standard list-of-dicts dataset.
- `PolarsDataset(df: polars.DataFrame)`: High-performance dataframe.
- `ArrowDataset(table: pyarrow.Table)`: Binary Apache Arrow memory sharing.
- `StreamingDataset(gen_fn, columns, estimated_count)`: Low-RAM iterator chunks.
- **Methods**: `.columns()`, `.to_list()`, `.row_count()`, `.to_polars()`, `.to_arrow()`.
