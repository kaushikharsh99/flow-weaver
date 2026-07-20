# ⚡ FlowWeaver Visual Compiler Architecture & SDK Guide

> **"FlowWeaver is a visual compiler that generates production-ready, zero-dependency Python preprocessing scripts."**
> 
> The visual editor is a frontend for writing Python. Execution is not a custom DAG runtime or worker queue — running `python pipeline.py` *is* the execution, with zero runtime or SDK dependencies.

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
     PipelineLinker        ── (AST parsing, dependency tracing, tree shaking)
           │
           ▼
   Python Code Generator    ── (Deduplicated imports, inlined helpers, formatting via AST unparse)
           │
           ▼
  Standalone pipeline/     ── (Independent, zip-distributable package)
     ├── pipeline.py
     ├── requirements.txt
     ├── config.yaml
     ├── README.md
     └── LICENSE
```

---

## 📦 FlowWeaver Standard Library (`flowweaver.std`)

The visual compiler treats the **FlowWeaver Standard Library (`flowweaver.std`)** as a source-only library. Rather than importing from it at runtime, the compiler's **Linker** parses the required functions, classes, and helper utilities directly from the SDK source using Python's `ast` module, resolving dependencies recursively and inlining the minimum reachable code directly into the compiled script.

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
- `ctx.dataset().strip_whitespace(column=..., collapse=...)`
- `ctx.dataset().strip_html(column=...)`
- `ctx.dataset().regex_replace(column=..., pattern=..., replacement=...)`
- `ctx.dataset().select_columns(columns=...)`
- `ctx.dataset().rename_columns(rename_map=...)`
- `ctx.dataset().drop_columns(columns=...)`
- `ctx.dataset().sort_rows(by=..., ascending=...)`
- `ctx.dataset().sample_rows(n=..., seed=...)`
- `ctx.dataset().shuffle(seed=...)`
- `ctx.dataset().split_dataset(ratio=..., seed=...)`
- `ctx.dataset().concatenate(other_var=...)`
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
⏱  Compile Time:       12.50 ms
📜 Generated LOC:      439 lines (including inlined stdlib)
📦 Operations Count:   3
📥 Imports Count:      2
🏷  Variables Count:    3
```

---

## 🎨 Generated Python Quality & Production Features

FlowWeaver compiles visual pipelines into professional, hand-written quality standalone Python scripts equipped with:

1. **Zero-Dependency Inlining & Tree Shaking**:
   - The compiler analyzes the AST of the required standard library operations, recursively extracts all helper functions, validation utils, and base/subclass `Dataset` classes, and inlines only the reachable code.
   - Deduplicates and merges all top-level imports into a single, clean block at the top of the file.

2. **Structured CLI Arguments (`argparse`)**:
   - Auto-detects input and output paths to generate `--input` and `--output` options.
   - Provides `--dry-run` and `--verbose` flags out-of-the-box.
   - Substitutes path string literals with `args.input` and `args.output` references dynamically.

3. **Step Progress & Logging**:
   - Sets up standard `logging` with structured formats: `HH:MM:SS [LEVEL] Message`.
   - Injects progress log tags for every pipeline step (e.g., `logger.info("Step 3/8: Normalize Text to Lowercase")`).

4. **Performance Metrics**:
   - Injects timestamps (`time.time()`) to track and report precise total execution times upon pipeline completion.

5. **Package Distribution Output (`pipeline/`)**:
   - Generates a standalone directory containing the `pipeline.py` script, `requirements.txt` listing any third-party dependencies, a configured `config.yaml`, a `LICENSE` file, and `sample_input/` / `sample_output/` folders.
   - Steps are separated by readable comment headers.
   - Python code is formatted with maximum clarity and uses semantic variable names instead of generic names.
