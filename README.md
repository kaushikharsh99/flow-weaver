# FlowWeaver 🚀

**FlowWeaver** is an open-source visual preprocessing and cleaning platform designed for AI and Machine Learning datasets. It provides researchers with a node-based infinite canvas to clean, filter, tokenize, and restructure data streams at scale without writing ad-hoc python scripts.

---

## Key Features

- **Infinite Visual Canvas**: Drag, drop, connect, and compile pipelines with real-time visual execution progress indicators, edge stats, and profiler metrics.
- **Node-as-Adapter Architecture**: Standardized, secure sandboxing separating visual adapter layouts (`node.py` under 200 lines) from pure Python business logic (`core/algorithm.py`).
- **20+ High-Fidelity Concrete Nodes**: Out-of-the-box support for loading/exporting CSV, JSON, JSONL, and Parquet (via Polars); text case mapping, HTML tag stripping, Unicode normalizations, word/sentence tokenizers, and sliding-window RAG document chunkers.
- **Advanced Deduplication**: Fast exact key filters, cryptographic xxHash/SHA256 digests, locality-sensitive **SimHash** near-duplicate Hamming distance filters, and **MinHash** Jaccard set permutations.
- **Dynamic Seeding & Templates**: Bootstrapped with 6 pre-positioned visual pipeline templates:
  - *LLM Fine-Tuning Prep*
  - *RAG Document Prep*
  - *TinyStories Dataset Cleaning*
  - *ShareGPT Preprocessing*
  - *OCR Post-Processing*
  - *Common Crawl Filtering*
- **Robust Quality Telemetry**: Actionable context-aware diagnostic cards for runtime errors, stage-based row transformation counters, and live websocket execution log streams.
- **Zero-Copy Dataset Engines**: Support for memory-shared `PolarsDataset`, PyArrow zero-copy `ArrowDataset`, and low-RAM batch generator `StreamingDataset` processing gigabyte-scale datasets under constant memory footings.
- **Enterprise Debugger & Profiler**: Dynamic debugger breakpoints with REST pause/resume routing, timing (ms), Peak RAM maximum resident set size (RSS) profiling, and throughput speeds.
- **Plugin Scaffolder CLI**: Integrated commands to create plugins, create category-specific boilerplate node templates, test configurations, lint constraints, and package verified plugins.
- **Dockerized sandbox dev environments** and onboarding validation quality gates.

---

## Directory Overview

```
flow-weaver/
├── apps/
│   ├── api/                 # FastAPI Backend Service & Engine
│   └── web/                 # React Frontend Client (Vite + ReactFlow)
├── packages/
│   └── flowweaver_sdk/      # Core Developer Python SDK (cli, node, context, dataset)
├── plugins/                 # Local dynamic plugins scan folder
├── scripts/                 # Developer Lifecycle Control Suite (install, run, doctor, test, clean)
└── docs/                    # Complete Markdown Portal & Reference Website
```

---

## Quick Start

### 1. Prerequisites
Ensure you have the following installed on your host system:
- **Python**: Version 3.12 or newer.
- **Node.js**: Version 20 or newer (npm or pnpm).

### 2. Run the Onboarding Setup
FlowWeaver includes an onboarding setup script that verifies dependencies, initializes python virtual environments, installs workspaces, and migrates SQLite databases:
```bash
python scripts/install.py
```

### 3. Run Development Servers
Start both backend API servers and frontend Vite client workspace concurrently:
```bash
python scripts/run.py
```
- **Web UI Client**: http://localhost:8080
- **Backend Swagger API docs**: http://localhost:8000/api/docs

### 4. Running Sandbox Containers (Docker)
Start the complete sandbox container environment with database volume mounts:
```bash
docker compose up --build
```

### 5. Running Diagnostics & Tests
Check configuration states and run smoke validation tests:
```bash
python scripts/doctor.py
python scripts/test.py
```

---

## Contributor Quality Gates

To ensure all dynamic nodes and changes meet monorepo standards before pushes, run the onboarding gate script:
```bash
python scripts/pre-commit-gate.py
```
This executes:
- Compiler topological planning tests.
- React TS workspace typechecks.
- Code style, line limits (under 200 lines), and sandboxing checks on custom plugins.

---

## Documentation Index

Explore our comprehensive portal guides under the `docs/` directory:
- 📖 [Portal Home](docs/README.md) — Documentation index and philosophy.
- 🚀 [Getting Started](docs/getting-started.md) — Visual canvas guide and first workflow.
- ⚙ [Installation Guide](docs/installation.md) — Detailed setup, configs, and env options.
- 💻 [SDK Reference](docs/sdk-reference.md) — Metaclass decorators, parameters, and datasets.
- 🛠 [Creating Custom Nodes](docs/creating-nodes.md) — Scaffolding nodes using the Node-as-Adapter pattern.
- 📦 [Plugin Development](docs/plugin-development.md) — Packaging and distributing plugins.
- 🛠 [CLI Reference](docs/cli-reference.md) — Options for `flowweaver` CLI commands.
- ❓ [FAQ & Troubleshooting](docs/faq.md) — Sandbox limits, big datasets, and errors.
