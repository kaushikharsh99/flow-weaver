# Steps Completed Log

This document records the exact milestones, phases, and files implemented during the FlowWeaver foundatonal refactoring sessions.

---

## Completed Milestones

### Phase 0 — Design Specs & Vision
- **VISION.md**: Defined FlowWeaver's core values ("Everything is a Node, Everything is a Plugin, Everything Streams, Versioned, Inspectable, Reproducible") and target monorepo roadmap.
- **ARCHITECTURE.md**: Documented the 7-layer architecture (Frontend → REST/WS API → Core Services → Execution Engine → Node Runtime → Plugins → DB/FS Storage) and migration path.
- **PIPELINE_FORMAT.md**: Finalized the `v1.0.0` JSON schema contract specifying nodes, edges, viewport, settings, and variables mapping.
- **NODE_SPEC.md**: Defined universal node lifecycle states and the execution context signature.
- **API_CONTRACT.md**: Outlined all 38 REST endpoints and websocket events.
- **ROADMAP.md**: Outlined a 9-phase execution timeline (Freeze Foundation → Dynamic Node SDK → Quality → Node Collection → Templates → Documentation → Team Scaling → Polish → Alpha).

### Phase 1 — Lock the Frontend
- Extracted all magic styling parameters, comment dimensions, grid sizes, and execution bounds into `constants.ts`.
- Created front-end API wrappers (`types.ts`, `client.ts`, `index.ts`) defining type contracts and the `createMockClient()` handler.
- Refactored `store.ts` to execute async operations (`savePipelineToServer`, `loadPipelineFromServer`, `createNewPipeline`), align `exportJSON`/`importJSON` with `v1.0.0` schemas, and store backend `projectId` and `pipelineId` attributes.

### Phase 2 — Monorepo Restructuring & Backend Scaffolding
- Migrated files into standard workspaces:
  - `apps/web`: Frontend Vite client.
  - `apps/api`: Backend FastAPI project.
- Configured root workspaces in `package.json` and type references in `tsconfig.json`.
- Scaffolded FastAPI with models (`models.py`), request schemas (`schemas.py`), endpoints (`routes/`), and database connection parameters (`db.py`).

### Phase 3 / 6 Compiler Layer Refactor (Staged execution planner)
- Designed and built a modular compiler subsystem in `apps/api/app/engine/compiler/`:
  - **`models.py`**: Pydantic models for `Task`, `ExecutionPlan`, and `ValidationError`.
  - **`validator.py`**: A **Semantic Validator** for syntax checks, connectivity validation, schema parameters validation, and cycle detection.
  - **`builder.py`**: A **Graph Builder** converting raw canvas JSON nodes/edges to dependency-sorted tasks.
  - **`optimizer.py`**: A **Graph Optimizer** for evaluating node pruning and checkpoint caching.
  - **`planner.py`**: An **Execution Planner** generating stage-based concurrent task execution profiles.
- Overhauled `runner.py` to compile raw pipelines prior to running, validating port configurations and staging concurrency loops.

### Phase 5 — Dynamic Node Registry
- Built the `NodeRegistry` in `apps/api/app/engine/registry.py` registering all 24 built-in nodes.
- Exposed registry definitions over `/api/nodes` routes.
- Created `getIcon` helper on the frontend (`nodeTypes.ts`) resolving Lucide Icons dynamically from backend string names.

### Phase 7 — HTTP API Client & WS Integration
- Built `http-client.ts` implementing the REST endpoints.
- Connected the frontend runner (`runner.ts`) to save local canvas states to the database and connect to the WS stream at `ws://localhost:8000/api/executions/{id}/stream` when starting execution.

### Setup, Run & Ignore Utilities
- Created `run.py` at the project root to automate virtual environment setups, install backend Python dependencies, install npm workspaces, and run frontend and backend servers concurrently.
- Configured python gitignores for `.pyc`, `venv/`, and `__pycache__` to keep commits clean.

### Milestone 2 — Core SDK & Dataset Abstraction
- Created the **Python Developer SDK** in `packages/flowweaver_sdk/flowweaver/sdk`:
  - `node.py`: Declarations for base `Node`, `Port`, and `Parameter`.
  - `dataset.py`: Memory-efficient `Dataset` abstraction and `TabularDataset` implementation.
  - `context.py`: `ExecutionContext` tracking logger strings and `Metrics` runtimes (ms).
  - `artifact.py`: Pydantic structural model for tracking pipeline assets.
- Installed `flowweaver-sdk` inside the backend `venv` (under editable `-e` flag).
- Refactored `apps/api/app/engine/nodes/` to import from SDK and return `Dataset` instances.
- Updated `runner.py` to compile nodes using the SDK node signature and serialize tabular dataset previews KNIME-style to render edge statistics on the frontend.

### Milestone 3 — Data Engine (Polars, PyArrow, Streaming Execution)
- Expanded the `Dataset` abstraction layer inside `flowweaver/sdk/dataset.py`:
  - Implemented `PolarsDataset` wrapping `polars.DataFrame` natively.
  - Implemented `ArrowDataset` wrapping `pyarrow.Table` for zero-copy memory operations.
  - Developed `StreamingDataset` mapping iterator/generator record chunks supporting large-scale file processing (GB/TB scale) under constant, low RAM footprint.
- Updated setup package configurations (`setup.py`) and virtual environment requirements (`requirements.txt`) to dynamically install and support `polars`, `pyarrow`, and `duckdb` binary wheels on Python 3.13.
- Created and executed a comprehensive automated dataset test pipeline verifying zero-copy data conversions and generator iterators.

### Milestone 4 — Developer Experience (CLI & Hot-Reload Loader)
- Created CLI plugin creator script `packages/flowweaver_sdk/flowweaver/sdk/cli.py` and mapped the console command `flowweaver` inside `setup.py` entry points.
- Implemented `load_local_plugins()` dynamic scan and loaders inside `registry.py` to load custom nodes dynamically from `plugins/` on startup.
- Scaffolded sample plugin `text_utils` inside `plugins/` via CLI, and successfully verified dynamic loading of `text_utils_processor` in registry node lists.

### Milestone 5 — Enterprise Debugger & Profiler
- Developed thread waker Event synchronization in `runner.py` supporting execution pauses at breakpoints (nodes carrying `__breakpoint__ = True`).
- Added REST routes `/api/executions/{id}/resume` and `/api/executions/{id}/pause` in `executions.py` to trigger debugger wake events.
- Added client interface signatures (`types.ts`, `client.ts`, `http-client.ts`, `mock-client.ts`) representing paused states, pause actions, and resume actions.
- Integrated runtime performance profiling inside `runner.py` calculating task elapsed durations (ms), Peak RAM memory allocations (bytes) utilizing Linux `resource` self RSS headers, and rows/second throughput.

---

## Session Refactoring Milestones (Phases 2-8 Complete)

### Node Boilerplate Category Scaffolding
- Added category-specific scaffolding inside the `flowweaver create-node` CLI parser, generating boilderplate templates tailored to `Loader`, `Filter`, `Transform`, `Exporter`, and `AI` node categories.
- Added automatic CSV and JSON mock dataset seeding (`data/sample.csv` and `data/sample.json`) on node creation to guarantee unit tests pass immediately out-of-the-box.
- Implemented pre-packaging constraints verifying style, lines limits, and sandbox imports inside the CLI `package_plugin` flow before archiving code.

### Robust Quality Framework
- Created custom `format_execution_error` context card mappings replacing raw tracebacks for Missing Columns (`KeyError` with column suggestions), Missing Files (`FileNotFoundError`), and Invalid Regex.
- Added pretty execution summaries logging stage row transformations (retained/removed counts).
- Connected progress hooks (`report_progress(percent, msg)`) and cancellation check triggers (`is_cancelled()`) inside SDK context.
- Populated advanced edge previews resolving tabular statistics (row counts, sizes) and column type schemas (`schema: { col: type }`).

### Production-Ready Node Library (20 Nodes)
- Built a reusable computational algorithms library `app/engine/nodes/core_logic.py` containing pure-python logic.
- Implemented 20 concrete built-in nodes:
  - *Loaders:* Load CSV, Load JSON, Load JSONL, Load Parquet (via Polars), Hugging Face Dataset.
  - *Cleaning:* Lowercase, Strip HTML, Remove Empty, Unicode Normalize, Regex Replace.
  - *Filters:* Filter Rows (Generic operator), Length Filter, Language Filter, Deduplicate Records.
  - *Transform:* Tokenize Text (Word/Sentence), Text Chunking (sliding window), Rename Columns.
  - *Export:* Write CSV, Write JSON Lines, Write Parquet, Upload HuggingFace.
- Removed duplicate overlaps in `stubs.py` keeping remainders isolated.
- Overhauled deduplication to support **SimHash** locality-sensitive fingerprints, **MinHash** Jaccard set permutations, and xxHash/SHA256 digests.

### Pre-Seeded Templates & Dynamic Selection
- Created `app/seed.py` seeding **6 default pipeline templates** on database boot.
- Positioned templates nodes on canvas coordinate grids for elegant layouts.
- Linked frontend Command Palette to load seeded templates dynamically via the templates API, clearing pipeline IDs to avoid editing original templates.

### Unified Sandboxes & Onboarding Quality Gates
- Created Dockerfiles for frontend (`apps/web`) and backend (`apps/api`) workspaces alongside root `docker-compose.yml` to launch sandbox containers out-of-the-box.
- Developed onboarding quality gate script `scripts/pre-commit-gate.py` that validates all compiler tests, frontend typechecks, and plugin lint checks before pushes.

### Visual & Premium Polish
- Added empty-state guidance card overlays in the infinite canvas wrapper.
- Refactored visual toolbar buttons to spring-motion elements with hover/click scaling effects.
- Cleaned up leftover branding (Flowline, Lovable) and removed `.lovable` project files.

### Refactoring Visual Compiler Platform (v0.1.0 Complete)
- **Compiler Subsystem Implementation (`apps/api/app/compiler/`)**:
  - Implemented Kahn's algorithm-based Topological Sorter.
  - Implemented `CompilerContext` with variable allocation managers (`variables.py`), dynamic import managers (`imports.py`), and a validator (`validator.py`).
  - Added Fluent SDK API wrapper (`DatasetRef` inside `context.py`) supporting simplified compilation definitions (`ctx.dataset().lowercase()`, etc.).
- **Argparse & Logging Code Generation (`generator.py`)**:
  - Standalone scripts now include standard `logging` setup, timed execution markers (`time.time()`), and a robust CLI argument parser configuration (`argparse`).
  - Auto-substitutes input and output path string literals with dynamic `args.input` and `args.output` CLI arguments.
  - Formatted generated code cleanly with numbered comment step headers (e.g. `# Step 1/8: Import Dataset`).
- **Standard Library Expansion (`flowweaver.std`)**:
  - Expanded `tabular/` operations: `drop_columns`, `sample_rows`, `shuffle`, `split_dataset`, `concatenate`, `statistics`.
  - Expanded `text/` operations: `strip_html`, `strip_whitespace`.
  - Migrated nodes `DropColumns`, `SortRows`, `Shuffle`, `SplitDataset`, `Concatenate`, `SampleRows` from stubs.py to real production adapters in `transform.py` and `filters.py`.
- **Packaging Pipeline Artifacts**:
  - Compiler outputs a structured package: stand-alone executable (`pipeline.py`), visual representation (`pipeline.json`), dependency lock file (`pipeline.lock`), compilation statistics metrics (`metadata.json`), and structured log directory.
- **Frontend Code Display & REST API Fixes**:
  - Implemented line numbers gutter, syntax coloring, and horizontal scrolling in frontend `CompileViewerModal.tsx`.
  - Resolved `Project` models serialization `PydanticSerializationError` 500 in `/api/projects` endpoint.

