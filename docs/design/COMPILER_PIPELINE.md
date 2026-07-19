# FlowWeaver Compiler Pipeline Specification

This document details the design of the FlowWeaver Compiler Pipeline, which transforms a visual Pipeline JSON description into a highly optimized, safe Execution Plan.

```
+---------------+      +--------------------+      +-----------------+
| Pipeline JSON | ---> | Semantic Validator | ---> |  Graph Builder  |
+---------------+      +--------------------+      +-----------------+
                                                            |
                                                            v
+------------------+      +-------------------+      +-----------------+
|     Executor     | <--- | Execution Planner | <--- | Graph Optimizer |
+------------------+      +-------------------+      +-----------------+
```

---

## 1. Pipeline Stages

### 1.1. Semantic Validator (`validator.py`)
Responsible for ensuring the pipeline is logically sound before scheduling execution.
- **Syntactic Validation**: Checks that the JSON adheres to the Schema (valid IDs, node formats, types).
- **Port Compatibility**: Checks that connected output ports have types compatible with input ports (e.g. `tabular` connected to `tabular` or `any`).
- **Connection Completeness**: Raises errors for required input ports left unconnected.
- **Parameter Validation**: Runs checks against parameter schemas (valid values, ranges, required fields).
- **Cycle Detection**: Validates that the graph is a Directed Acyclic Graph (DAG) with no cycles.

### 1.2. Graph Builder (`builder.py`)
Builds a logical representation of the graph.
- Maps JSON node lists to internal `LogicalNode` models.
- Links ports to `LogicalEdge` objects.
- Constructs the raw logical dependency DAG.

### 1.3. Graph Optimizer (`optimizer.py`)
Optimizes the logical DAG for performance and resource usage.
- **Sub-graph Pruning**: Discovers and removes disabled nodes and any downstream branches that rely solely on pruned inputs.
- **Caching Detection**: Checks execution history or file checkpoints to mark nodes that can reuse cached outputs.
- **Node Fusion (Future)**: Fuse successive mapping transformations into single operation threads to minimize CPU/IO roundtrips.

### 1.4. Execution Planner (`planner.py`)
Compiles the optimized DAG into a list of execution steps (tasks).
- **Step Generation**: Emits an ordered list of task groups. Tasks in the same group can run concurrently.
- **Resource Allocation**: Sets resource profiles and parallelism bounds (e.g. `maxConcurrency`).
- **Plan Outputs**: Produces a serialized `ExecutionPlan` detailing the execution sequence, parameters, and cache checkpoints.

---

## 2. Model Schema Specification (Pydantic)

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ValidationError(BaseModel):
    node_id: Optional[str] = None
    level: str  # "error", "warning", "info"
    message: str

class ValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationError] = []

class Task(BaseModel):
    id: str
    node_id: str
    type_id: str
    parameters: Dict[str, Any]
    dependencies: List[str]  # Upstream task IDs that must complete first
    inputs: Dict[str, str]   # Maps input port -> upstream task output port
    is_cached: bool = False

class ExecutionPlan(BaseModel):
    id: str
    pipeline_id: str
    stages: List[List[Task]]  # List of concurrent task groups (stages)
    variables: Dict[str, Any]
```
