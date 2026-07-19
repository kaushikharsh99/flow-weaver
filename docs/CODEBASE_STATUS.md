# FlowWeaver Codebase Status

This document serves as the developer handbook and codebase snapshot for FlowWeaver. Read this first to understand the system design, file layout, and structural contracts before making updates.

---

## 1. Directory Structure

FlowWeaver is structured as a workspace-based monorepo:

```
flow-weaver/
├── apps/
│   ├── api/                 # FastAPI Backend Service
│   │   ├── app/
│   │   │   ├── engine/      # Core Execution Engine & Node Registry
│   │   │   │   ├── compiler/# Compiler Pipeline Subsystem
│   │   │   │   │   ├── builder.py    # Converts JSON to logical DAG Tasks
│   │   │   │   │   ├── models.py     # Pydantic compile-time schemas
│   │   │   │   │   ├── optimizer.py  # Cache/Checkpoints optimization rules
│   │   │   │   │   ├── planner.py    # Generates layered execution plans
│   │   │   │   │   └── validator.py  # Run cycles & semantic safety checks
│   │   │   │   ├── nodes/   # Individual Python Node Implementations
│   │   │   │   ├── base.py
│   │   │   │   ├── registry.py  # Standard registry + local dynamic plugin loader
│   │   │   │   └── runner.py    # Sequential DAG executor supporting breakpoints & profiling metrics
│   │   │   ├── routes/      # REST API Routers & WS Channels (executions.py exposes pause/resume)
│   │   │   ├── db.py        # SQLAlchemy context setup
│   │   │   ├── models.py    # Database models (SQLite/Postgres)
│   │   │   └── schemas.py   # Pydantic schemas
│   │   ├── main.py          # FastAPI server entry point
│   │   └── requirements.txt
│   └── web/                 # React Frontend Client
│       ├── src/
│       │   ├── api/         # Front-end API Client bindings (HTTP & Mock)
│       │   ├── pipeline/    # Core canvas components, store, and execution runner
│       │   │   ├── components/
│       │   │   ├── constants.ts
│       │   │   ├── nodeTypes.ts
│       │   │   ├── runner.ts
│       │   │   ├── store.ts
│       │   │   └── types.ts
│       │   ├── styles.css
│       │   └── ...
│       ├── package.json
│       └── vite.config.ts
├── packages/                # Shared packages
│   └── flowweaver_sdk/      # Core Python Developer SDK
│       ├── flowweaver/
│       │   ├── __init__.py
│       │   └── sdk/
│       │       ├── __init__.py
│       │       ├── artifact.py  # Artifact models
│       │       ├── cli.py       # Plugin generator command parser
│       │       ├── context.py   # ExecutionContext, Logger, Metrics
│       │       ├── dataset.py   # Dataset, TabularDataset, PolarsDataset, ArrowDataset, StreamingDataset
│       │       └── node.py      # Base Node, Port, Parameter definitions
│       └── setup.py
├── plugins/                 # Local dynamic plugins directory (scanned on boot)
│   └── text_utils/          # Sample CLI-generated plugin
├── scripts/                 # Developer Lifecycle Control Suite
│   ├── clean.py             # Remove compiler and packaging caches
│   ├── doctor.py            # Environment checklist verification
│   ├── install.py           # Onboarding setups (venv, npm install, DB schemas)
│   ├── run.py               # Concurrently starts dev servers
│   └── test.py              # Smoke test compilation & registry checks
├── package.json             # Root monorepo workspace configuration
├── tsconfig.json            # Root tsconfig path mapping
└── run.py                   # Waker runner entry script (forwards to scripts/run.py)
```

---

## 2. API Contract & Persistence Config

The client interfaces communicate with the backend using the standard `ApiClient` interface (`apps/web/src/api/client.ts`).

### Toggle between Mock and Real APIs
You can toggle the frontend client between mock (in-memory) state and real HTTP backend queries using the environment variable `VITE_USE_MOCK_API`:
- **Mock Mode** (`VITE_USE_MOCK_API=true`): Frontend uses `mock-client.ts` storing data in memory maps and running simulated delays.
- **HTTP Mode** (`VITE_USE_MOCK_API=false`): Frontend uses `http-client.ts` to call REST routes on `http://localhost:8000/api` and websockets on `ws://localhost:8000/api/executions/{id}/stream`.

---

## 3. Node Registry & Dynamic Plugin Loader

The registry is the source of truth for available nodes, ports, and configuration options.
- **Backend Registry** (`apps/api/app/engine/registry.py`): Implements `NodeRegistry` with 24 built-in nodes.
- **Dynamic Plugin Scanning**: Upon server boot (`main.py`), the registry calls `.load_local_plugins("plugins")`. It scans folders under the `plugins/` directory, parses their `plugin.yaml` manifest, and dynamically imports declared custom node classes at runtime using `importlib`.
- **Frontend Integration**: Node list and parameters are retrieved dynamically from the `/api/nodes` route. Icons are resolved dynamically in components (`Sidebar.tsx`, `Inspector.tsx`, `NodeViews.tsx`) using the `getIcon()` utility.

---

## 4. Database Schema (SQLite)

Configured in `apps/api/app/models.py`. Standard tables:
- **`projects`**: Holds list of workspaces.
- **`pipelines`**: Holds JSON nodes, edges, viewport, variables, and settings.
- **`executions`**: Tracks active background runner status and logs.
- **`templates`**: Holds reusable pipeline structures.

---

## 5. Developer Lifecycle Control Suite (`scripts/`)

Instead of mixing setup tasks during dev servers execution, project lifecycle commands are modularly segregated:

- **`install.py`**: Runs once to perform initial environment setups. Creates the python virtual environment (`venv`), upgrades pip, installs package dependencies, configures `.env`, and initializes SQLite database tables.
- **`run.py`**: Assumes project setup is complete. Concurrently launches Uvicorn API server and Vite Web client, prefixing stdout streams cleanly (`[API]` / `[WEB]`) and listening for termination interrupts.
- **`doctor.py`**: Runs diagnostic checklist verifying dependency imports, environment files, free ports, Node/Python levels, and SQLite schema state.
- **`test.py`**: Execution test suite testing semantic validators, planners, DAG compilers, and checking frontend type safety compiles clean.
- **`clean.py`**: Deletes `__pycache__` artifacts, `.pytest_cache`, and Vite/setuptools caching build structures.

---

## 6. Compiler Pipeline (Plan & Compilation)

FlowWeaver compiles visual pipelines prior to running them:

1. **Semantic Validator** (`validator.py`): Validates schemas, parameters, required inputs connectivity, and checks for DAG cycles.
2. **Graph Builder** (`builder.py`): Translates raw JSON representation into logical tasks mapping input-to-output handles.
3. **Graph Optimizer** (`optimizer.py`): Evaluates caching rules, checkpoint states, and disabled tasks.
4. **Execution Planner** (`planner.py`): Organizes execution into sequential stages, separating concurrent tasks.
5. **DAG Executor** (`runner.py`): Consumes plan stages and executes tasks, streaming logs and updates via WebSockets.

---

## 7. Core Developer SDK (`packages/flowweaver_sdk`)

The SDK separates the platform backend from individual node logic:

- **CLI Tool** (`cli.py`): Bundles a `flowweaver create-plugin <name>` scaffolding tool. It generates fully structured, boilerplate plugin packages containing `plugin.yaml` manifests, `requirements.txt`, and sample node code.
- **Dataset Abstraction** (`dataset.py`): Exposes multiple underlying engines wrapper implementations:
  - `TabularDataset`: Memory list of row dictionaries.
  - `PolarsDataset`: Wraps Polars DataFrame for highly optimized native parallel query operations.
  - `ArrowDataset`: Wraps PyArrow table representing zero-copy columns.
  - `StreamingDataset`: Generator-based row/chunk batch iterator supporting large files (GBs/TBs) with low, constant RAM overhead.
- **Base Node Class** (`node.py`): Defines developer interface models `Node`, `Port`, and `Parameter` utilizing Pydantic constraints.
- **Execution Context** (`context.py`): Wraps runtime services inside `ExecutionContext` including `Logger` tracking logs, and `Metrics` (automatically calculating execution duration milliseconds).
- **Artifact System** (`artifact.py`): Declares structural models representing execution assets (datasets, files, or custom JSON structures).

---

## 8. Enterprise Debugger & Profiler

FlowWeaver implements full debugger breakpoint pauses and resource execution profiling:

- **Debugger Breakpoint Pauses** (`runner.py` / `executions.py`): If a node contains `__breakpoint__ = True` (or execution status is paused), the background execution thread blocks using a `threading.Event` primitive. Rest routes `/api/executions/{id}/resume` and `/api/executions/{id}/pause` trigger waker signals.
- **Task Profiler Metrics** (`runner.py`): Computes precise task execution performance profiles:
  - Timing: tracks precise elapsed execution duration in milliseconds.
  - Memory: queries resident memory set sizes (RSS) maxrss utilizing Linux `resource` headers to calculate peak RAM allocation bytes.
  - Throughput: calculates rows processed per second dynamically from dataset row counts.
  - Preview payloads and metrics are emitted inside the `NODE_UPDATE` WebSocket frames to be mapped by the React client.
