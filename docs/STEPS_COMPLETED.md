# Steps Completed Log

This document records the exact milestones, phases, and files implemented during the FlowWeaver foundational refactoring session.

---

## Completed Milestones

### Phase 0 — Design Specs & Vision
- **VISION.md**: Defined FlowWeaver's core values ("Everything is a Node, Everything is a Plugin, Everything Streams, Versioned, Inspectable, Reproducible") and target monorepo roadmap.
- **ARCHITECTURE.md**: Documented the 7-layer architecture (Frontend → REST/WS API → Core Services → Execution Engine → Node Runtime → Plugins → DB/FS Storage) and migration path.
- **PIPELINE_FORMAT.md**: Finalized the `v1.0.0` JSON schema contract specifying nodes, edges, viewport, settings, and variables mapping.
- **NODE_SPEC.md**: Defined universal node lifecycle states and the execution context signature.
- **API_CONTRACT.md**: Outlined all 38 REST endpoints and websocket events.
- **ROADMAP.md**: Outlined a 4-milestone execution timeline (MVP → Alpha → Beta → v1.0).

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
