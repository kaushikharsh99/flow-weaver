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
│   │   │   │   ├── registry.py
│   │   │   │   └── runner.py
│   │   │   ├── routes/      # REST API Routers & WS Channels
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
│       ├── flowweaver/sdk/
│       │   ├── __init__.py
│       │   ├── artifact.py  # Artifact models
│       │   ├── context.py   # ExecutionContext, Logger, Metrics
│       │   ├── dataset.py   # Dataset & TabularDataset abstractions
│       │   └── node.py      # Base Node, Port, Parameter definitions
│       └── setup.py
├── plugins/                 # Dynamic plugins/nodes (future)
├── package.json             # Root monorepo workspace configuration
├── tsconfig.json            # Root tsconfig path mapping
└── run.py                   # Dev server orchestrator script (handles venv/npm setups)
```

---

## 2. API Contract & Persistence Config

The client interfaces communicate with the backend using the standard `ApiClient` interface (`apps/web/src/api/client.ts`).

### Toggle between Mock and Real APIs
You can toggle the frontend client between mock (in-memory) state and real HTTP backend queries using the environment variable `VITE_USE_MOCK_API`:
- **Mock Mode** (`VITE_USE_MOCK_API=true`): Frontend uses `mock-client.ts` storing data in memory maps and running simulated delays.
- **HTTP Mode** (`VITE_USE_MOCK_API=false`): Frontend uses `http-client.ts` to call REST routes on `http://localhost:8000/api` and websockets on `ws://localhost:8000/api/executions/{id}/stream`.

---

## 3. Node Registry System

The registry is the source of truth for available nodes, ports, and configuration options.
- **Backend Registry** (`apps/api/app/engine/registry.py`): Implements `NodeRegistry` with 24 built-in nodes.
- **Frontend Integration**: Node list and parameters are retrieved dynamically from the `/api/nodes` route. Icons are resolved dynamically in components (`Sidebar.tsx`, `Inspector.tsx`, `NodeViews.tsx`) using the `getIcon()` utility.

---

## 4. Database Schema (SQLite)

Configured in `apps/api/app/models.py`. Standard tables:
- **`projects`**: Holds list of workspaces.
- **`pipelines`**: Holds JSON nodes, edges, viewport, variables, and settings.
- **`executions`**: Tracks active background runner status and logs.
- **`templates`**: Holds reusable pipeline structures.

---

## 5. Dev Orchestration

To run the full stack concurrently, execute `./run.py` at the root folder. It sets up the python virtual environment, installs dependencies, and runs Vite and Uvicorn.

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

- **Dataset Abstraction** (`dataset.py`): Wraps tabular data representation inside `Dataset` and `TabularDataset` interfaces. Prevents coupling nodes with specific structures (e.g. Polars, Arrow, list-of-dicts) by exposing a unified `.to_list()` and `.columns()` protocol.
- **Base Node Class** (`node.py`): Defines developer interface models `Node`, `Port`, and `Parameter` utilizing Pydantic constraints.
- **Execution Context** (`context.py`): Wraps runtime services inside `ExecutionContext` including `Logger` tracking logs, and `Metrics` (automatically calculating execution duration milliseconds).
- **Artifact System** (`artifact.py`): Declares structural models representing execution assets (datasets, files, or custom JSON structures).
