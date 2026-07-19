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

### Phase 5 — Dynamic Node Registry
- Built the `NodeRegistry` in `apps/api/app/engine/registry.py` registering all 24 built-in nodes.
- Exposed registry definitions over `/api/nodes` routes.
- Created `getIcon` helper on the frontend (`nodeTypes.ts`) resolving Lucide Icons dynamically from backend string names.

### Phase 6 — Backend Execution Engine
- Implemented Kahn's Topological Sort cycle detector in `apps/api/app/engine/runner.py`.
- Developed actual execution logic for data loading (`LoadCSV`, `LoadJSON`), filtering (`FilterRows`), and exporting (`WriteCSV`) along with simulated handlers for fallbacks.
- Integrated websocket progress alerts inside `executions.py` running the engine inside a background worker thread.

### Phase 7 — HTTP API Client & WS Integration
- Built `http-client.ts` implementing the REST endpoints.
- Connected the frontend runner (`runner.ts`) to save local canvas states to the database and connect to the WS stream at `ws://localhost:8000/api/executions/{id}/stream` when starting execution.

### Setup and Running Utilities
- Created `run.py` at the project root to automate virtual environment setups, install backend Python dependencies, install npm workspaces, and run frontend and backend servers concurrently.
