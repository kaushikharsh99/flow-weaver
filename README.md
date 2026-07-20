# FlowWeaver

FlowWeaver is a node-based editor for cleaning and preprocessing datasets before they go into ML training or RAG pipelines. Instead of writing another one-off `clean_data.py` script, you wire together nodes on a canvas — load a file, filter rows, dedupe, tokenize, export — and run the whole thing with live progress and row counts as it executes.

It started as a way to avoid rewriting the same pandas boilerplate for every new dataset. The current version handles CSV/JSON/JSONL/Parquet, common text cleaning steps, and a few dataset-specific things like near-duplicate detection that are annoying to hand-roll.

## Why

Most dataset cleaning ends up as a pile of scripts that only the person who wrote them understands, run in an order nobody wrote down. FlowWeaver makes that pipeline visible and re-runnable: each node does one thing, you can see how many rows survive each step, and the whole pipeline is a JSON file you can check into git or hand to a teammate.

## What's in the box

- **Canvas editor** (React + React Flow) for building pipelines by connecting nodes, with live execution status per node and a log stream over websockets.
- **~20 built-in nodes**: loaders/exporters for CSV, JSON, JSONL and Parquet (via Polars); text cleanup (case normalization, HTML stripping, Unicode normalization); tokenizers; a sliding-window chunker for RAG documents; and dedup nodes ranging from exact-key matching to SimHash/MinHash-based near-duplicate filtering.
- **Node = adapter, logic = plain Python.** Each node's UI-facing code stays under ~200 lines and just wraps a plain function in `core/algorithm.py`. That split is intentional — the algorithm doesn't know or care that it's running inside a node.
- **Three dataset backends** depending on size: an in-memory Polars dataset for the common case, an Arrow zero-copy variant, and a streaming/batched dataset for files that don't fit in RAM.
- **A debugger** — set breakpoints on nodes, pause mid-run, inspect the data at that point, resume.
- **A plugin CLI** (`flowweaver`) for scaffolding new nodes, running their tests, and packaging them for distribution.
- **6 starter templates** (fine-tuning prep, RAG document prep, TinyStories cleanup, ShareGPT preprocessing, OCR post-processing, Common Crawl filtering) so you're not staring at a blank canvas.

## Project layout

```
flow-weaver/
├── apps/
│   ├── api/            FastAPI backend — the pipeline engine, compiler, node registry
│   └── web/             React frontend (Vite + React Flow + shadcn/ui)
├── packages/
│   └── flowweaver_sdk/  The Python SDK plugin authors build against (Node, Param, Dataset classes)
├── plugins/              Local plugins get picked up from here automatically
├── scripts/               install / run / doctor / test / clean — see below
└── docs/                  Longer docs: architecture, node spec, SDK reference
```

## Getting started

You'll need Python 3.12+ and Node 20+.

```bash
python scripts/install.py   # sets up the venv, installs both workspaces, runs DB migrations
python scripts/run.py        # starts the API and the web client together
```

- Web UI: http://localhost:8080
- API + Swagger docs: http://localhost:8000/api/docs

If something's not working, `python scripts/doctor.py` checks the usual culprits (Python/Node versions, missing deps, DB state) before you go digging manually.

Prefer Docker?

```bash
docker compose up --build
```

### Running the tests

```bash
python scripts/test.py
```

There's also `scripts/pre-commit-gate.py`, which runs the same checks CI does — compiler tests, frontend typecheck, and the line-limit/sandboxing lint on plugin code — so you can catch failures before pushing instead of after.

## Writing a custom node

A node is two files: a thin adapter (`node.py`) describing inputs, outputs and parameters, and a plain Python function it calls (`core/algorithm.py`). The scaffolder gets you a working skeleton:

```bash
flowweaver create-node my_plugin --category filters
```

See [`docs/creating-nodes.md`](docs/creating-nodes.md) for the full contract (what a node is allowed to import, how sandboxing works, what counts as a valid `execute()` return value), and [`docs/plugin-development.md`](docs/plugin-development.md) if you want to package and share what you've built.

## Documentation

- [Getting started](docs/getting-started.md)
- [Installation, in more detail](docs/installation.md)
- [Architecture](docs/design/ARCHITECTURE.md)
- [Pipeline JSON format](docs/specs/PIPELINE_FORMAT.md)
- [Node spec](docs/specs/NODE_SPEC.md)
- [SDK reference](docs/sdk-reference.md)
- [CLI reference](docs/cli-reference.md)
- [FAQ](docs/faq.md)

## Status

This is an early, actively-changing project — expect rough edges, and expect the pipeline format to still shift a bit before it settles. Issues and PRs welcome; see [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for the ground rules (mainly: keep node adapters thin, put logic in `core/`, and don't skip the pre-commit gate).
