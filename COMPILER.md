# ⚡ FlowWeaver Visual Compiler Architecture & SDK Guide

> **"FlowWeaver is a visual compiler that generates production-ready Python preprocessing scripts."**
> 
> The visual editor is a frontend for writing Python. Execution is not a custom DAG runtime or worker queue — running `python pipeline.py` *is* the execution.

---

## 🏛️ Compiler Pipeline Architecture

```text
Visual Canvas (pipeline.json)
           │
           ▼
    PipelineValidator      ── (Cycles, disconnected nodes, missing parameters)
           │
           ▼
 Topological DAG Sort      ── (Kahn's algorithm)
           │
           ▼
   PipelineIR & Context    ── (Variable allocation, std library mapping)
           │
           ▼
  Python Code Generator    ── (Imports, function calls, formatting via AST unparse)
           │
           ▼
  Standalone pipeline.py   ── (Independent, version-controllable script)
```

---

## 📦 FlowWeaver Standard Library (`flowweaver.std`)

The visual compiler targets the **FlowWeaver Standard Library (`flowweaver.std`)**, a pure, standalone Python library for dataset engineering:

```python
from flowweaver.std.io import import_dataset, export_jsonl
from flowweaver.std.text import lowercase, unicode_normalize
from flowweaver.std.tabular import filter_rows

dataset = import_dataset("raw_data.csv")
dataset_1 = lowercase(dataset, column="instruction")
dataset_2 = unicode_normalize(dataset_1, column="instruction", form="NFC")
dataset_3 = filter_rows(dataset_2, column="instruction", operator="not_null")
export_jsonl(dataset_3, "clean_dataset.jsonl")
```

### Module Structure
- `flowweaver.std.datasets`: `Dataset` base class, `TabularDataset`, `PolarsDataset`, `ArrowDataset`, `StreamingDataset`, `DatasetSchema`, `DatasetMetadata`, and immutable `OperationRecord` history tracking.
- `flowweaver.std.io`: `import_dataset`, `export_csv`, `export_json`, `export_jsonl`, `export_parquet`.
- `flowweaver.std.text`: `lowercase`, `uppercase`, `unicode_normalize`, `strip_whitespace`, `regex_replace`.
- `flowweaver.std.tabular`: `select_columns`, `rename_columns`, `filter_rows`, `sort_rows`.
- `flowweaver.std.dedup`: `dedup_exact`, `simhash_deduplicate`.
- `flowweaver.std.utils`: `validate_dataset`, `validate_column_exists`, `validate_columns_exist`, `validate_not_empty`, `get_logger`, `ProgressTracker`.

---

## 🛠️ Compiler Context & SDK API

Node authors implement the `compile(self, ctx)` method on their node adapter class using the fluent `CompilerContext` SDK API.

### Fluent Dataset SDK (`ctx.dataset()`)

```python
from flowweaver.sdk import Node, Input, Output, Param, node

@node(name="Lowercase Text", category="Transform")
class LowercaseNode(Node):
    id = "lowercase"
    column = Param.column(label="Target Column", default="text")

    def compile(self, ctx):
        col = ctx.current_params.get("column", "text")
        return ctx.dataset().lowercase(column=col)
```

### Chained Operation Methods on `ctx.dataset()`
- `ctx.dataset().lowercase(column=...)`
- `ctx.dataset().uppercase(column=...)`
- `ctx.dataset().unicode_normalize(column=..., form=...)`
- `ctx.dataset().strip_whitespace(column=...)`
- `ctx.dataset().regex_replace(column=..., pattern=..., replacement=...)`
- `ctx.dataset().select_columns(columns=...)`
- `ctx.dataset().rename_columns(rename_map=...)`
- `ctx.dataset().filter_rows(column=..., operator=..., value=...)`
- `ctx.dataset().sort_rows(by=..., ascending=...)`
- `ctx.dataset().dedup_exact(columns=...)`
- `ctx.dataset().simhash_deduplicate(column=..., threshold=...)`
- `ctx.dataset().export_csv(path=...)`
- `ctx.dataset().export_jsonl(path=...)`
- `ctx.dataset().export_parquet(path=...)`

### Direct Helper Calls (`ctx.call()`)

For custom or external standard library functions:

```python
ctx.call("flowweaver.std.text.lowercase", ctx.input_var, column=col)
```

---

## 🖥️ CLI Developer Experience & Debug Mode

### Compiling Pipelines via Terminal

```bash
flowweaver compile pipeline.json --output pipeline.py
```

### Compiler Inspector & Diagnostics (`--debug`)

```bash
flowweaver compile pipeline.json --debug
```

Outputs:
```text
==================================================
         FlowWeaver Compiler Inspector Diagnostics
==================================================
⏱  Compile Time:       0.75 ms
📜 Generated LOC:      22 lines
📦 Operations Count:   5
📥 Imports Count:      3
🏷  Variables Count:    5

==================================================
Generated Python Output Preview:
==================================================
"""
FlowWeaver Generated Preprocessing Script
Pipeline: tpl_llm_finetuning
"""

from flowweaver.std.io import export_jsonl, import_dataset
from flowweaver.std.text import lowercase, unicode_normalize

def main():
    dataset = import_dataset(path='data/sample.csv')
    dataset_1 = lowercase(dataset, column='name')
    dataset_2 = unicode_normalize(dataset_1, column='name', form='NFC')
    dataset_3 = export_jsonl(dataset_2, path='out/finetuning_prep.jsonl')

if __name__ == '__main__':
    main()
```
