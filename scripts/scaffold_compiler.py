import os

# Base directory for the compiler package
compiler_base = "apps/api/app/engine/compiler"
os.makedirs(compiler_base, exist_ok=True)

# 1. Write __init__.py
init_py = """# FlowWeaver Compiler Subsystem
"""
with open(f"{compiler_base}/__init__.py", "w") as f:
    f.write(init_py)

# 2. Write models.py
models_py = """from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ValidationError(BaseModel):
    node_id: Optional[str] = Field(None, alias="nodeId")
    level: str  # error, warning, info
    message: str

    class Config:
        populate_by_name = True

class ValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationError] = []

class Task(BaseModel):
    id: str  # Task ID (typically same as node_id)
    node_id: str = Field(..., alias="nodeId")
    type_id: str = Field(..., alias="typeId")
    parameters: Dict[str, Any]
    dependencies: List[str]  # List of task IDs this task depends on
    inputs: Dict[str, Dict[str, str]]  # Maps: target_port -> {"source_node": "...", "source_port": "..."}
    is_cached: bool = Field(False, alias="isCached")

    class Config:
        populate_by_name = True

class ExecutionPlan(BaseModel):
    id: str
    pipeline_id: str = Field(..., alias="pipelineId")
    stages: List[List[Task]]  # Task layers that can run concurrently
    variables: Dict[str, Any]

    class Config:
        populate_by_name = True
"""
with open(f"{compiler_base}/models.py", "w") as f:
    f.write(models_py)

# 3. Write validator.py
validator_py = """from typing import List, Dict, Any
from app.engine.compiler.models import ValidationResult, ValidationError
from app.engine.registry import registry

def validate_pipeline(pipeline_data: Dict[str, Any]) -> ValidationResult:
    \"\"\"Run comprehensive semantic validation checks on the pipeline DAG.\"\"\"
    nodes = pipeline_data.get("nodes", [])
    edges = pipeline_data.get("edges", [])
    issues: List[ValidationError] = []
    
    # 1. Validate Syntactic structure & duplicate IDs
    node_ids = set()
    node_map = {}
    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            issues.append(ValidationError(level="error", message="Missing node ID in pipeline definition."))
            continue
        if node_id in node_ids:
            issues.append(ValidationError(nodeId=node_id, level="error", message=f"Duplicate node ID detected: '{node_id}'."))
        node_ids.add(node_id)
        node_map[node_id] = node

    # 2. Port Connectivity Check
    # Gathers which input handles have incoming connections
    connected_inputs: Dict[str, Set[str]] = {nid: set() for nid in node_ids}
    for edge in edges:
        target = edge.get("target")
        target_handle = edge.get("targetHandle")
        if target in connected_inputs and target_handle:
            connected_inputs[target].add(target_handle)

    # 3. Verify parameters and port dependencies against registry
    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("type")
        if node_type == "commentNode":
            continue
            
        data = node.get("data", {})
        type_id = data.get("typeId")
        params = data.get("params", {})
        disabled = data.get("disabled", False)
        
        if disabled:
            continue
            
        if not type_id:
            issues.append(ValidationError(nodeId=node_id, level="error", message="Node missing typeId definition."))
            continue
            
        reg_node = registry.get(type_id)
        if not reg_node:
            issues.append(ValidationError(nodeId=node_id, level="error", message=f"Unknown node type: '{type_id}'."))
            continue
            
        # Validate required inputs are connected
        for port in reg_node.inputs:
            if port.required and port.id not in connected_inputs.get(node_id, set()):
                issues.append(ValidationError(
                    nodeId=node_id, 
                    level="error", 
                    message=f"Required input port '{port.label}' ({port.id}) is not connected."
                ))
                
        # Validate parameters against validation schema rules
        valid, param_errors = registry.validate_config(type_id, params)
        if not valid:
            for err in param_errors:
                issues.append(ValidationError(nodeId=node_id, level="error", message=err))

    # 4. Cycle Detection (Topological Sort test)
    # Check only active nodes (exclude comments & disabled nodes)
    active_nodes = [n for n in nodes if n.get("type") != "commentNode" and not n.get("data", {}).get("disabled", False)]
    active_ids = {n["id"] for n in active_nodes}
    active_edges = [e for e in edges if e.get("source") in active_ids and e.get("target") in active_ids]
    
    indegree = {nid: 0 for nid in active_ids}
    adjacency = {nid: [] for nid in active_ids}
    for edge in active_edges:
        src = edge["source"]
        tgt = edge["target"]
        adjacency[src].append(tgt)
        indegree[tgt] += 1
        
    queue = [nid for nid, deg in indegree.items() if deg == 0]
    visited_count = 0
    while queue:
        curr = queue.pop(0)
        visited_count += 1
        for neighbor in adjacency[curr]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
                
    if visited_count != len(active_ids):
        issues.append(ValidationError(level="error", message="Cyclic connection loop detected in pipeline."))

    # Valid is true if no issues carry severity level of 'error'
    has_errors = any(issue.level == "error" for issue in issues)
    return ValidationResult(valid=not has_errors, issues=issues)
"""
with open(f"{compiler_base}/validator.py", "w") as f:
    f.write(validator_py)

# 4. Write builder.py
builder_py = """from typing import Dict, Any, List
from app.engine.compiler.models import Task

def build_tasks(pipeline_data: Dict[str, Any]) -> List[Task]:
    \"\"\"Convert nodes & edges into intermediate logical Tasks with explicit dependency listings.\"\"\"
    nodes = pipeline_data.get("nodes", [])
    edges = pipeline_data.get("edges", [])
    
    # Track only active non-comment nodes
    active_nodes = [n for n in nodes if n.get("type") != "commentNode" and not n.get("data", {}).get("disabled", False)]
    active_ids = {n["id"] for n in active_nodes}
    active_edges = [e for e in edges if e.get("source") in active_ids and e.get("target") in active_ids]
    
    # Map upstream target port links
    # node_id -> { target_port_id -> { "source_node": "...", "source_port": "..." } }
    input_mapping: Dict[str, Dict[str, Dict[str, str]]] = {nid: {} for nid in active_ids}
    dependencies: Dict[str, List[str]] = {nid: [] for nid in active_ids}
    
    for edge in active_edges:
        src = edge["source"]
        tgt = edge["target"]
        src_port = edge["sourceHandle"]
        tgt_port = edge["targetHandle"]
        
        input_mapping[tgt][tgt_port] = {
            "source_node": src,
            "source_port": src_port
        }
        dependencies[tgt].append(src)
        
    tasks = []
    for node in active_nodes:
        node_id = node["id"]
        node_data = node.get("data", {})
        
        task = Task(
            id=node_id,
            nodeId=node_id,
            typeId=node_data.get("typeId", ""),
            parameters=node_data.get("params", {}),
            dependencies=dependencies[node_id],
            inputs=input_mapping[node_id],
            isCached=False
        )
        tasks.append(task)
        
    return tasks
"""
with open(f"{compiler_base}/builder.py", "w") as f:
    f.write(builder_py)

# 5. Write optimizer.py
optimizer_py = """from typing import List, Dict, Any
from app.engine.compiler.models import Task

def optimize_tasks(tasks: List[Task], pipeline_data: Dict[str, Any]) -> List[Task]:
    \"\"\"Apply DAG compiler optimizations (e.g. checkpoint reuse, redundant node pruning).\"\"\"
    # Feature 1: Checkpoint Caching Check
    # For now, we mock caching evaluation by checking if nodes are configured for cache
    # or have run successfully in cache before (in production, we compare input checksums).
    for task in tasks:
        # Check if node has a custom cache settings config
        params = task.parameters
        if params.get("use_cache") is True or params.get("__cached__") is True:
            task.is_cached = True
            
    return tasks
"""
with open(f"{compiler_base}/optimizer.py", "w") as f:
    f.write(optimizer_py)

# 6. Write planner.py
planner_py = """import uuid
from typing import List, Dict, Any
from app.engine.compiler.models import Task, ExecutionPlan

def generate_plan(tasks: List[Task], pipeline_data: Dict[str, Any]) -> ExecutionPlan:
    \"\"\"Organize logical Tasks into execution stages (layers of concurrency).\"\"\"
    stages: List[List[Task]] = []
    
    # Copy task list to mutate
    remaining_tasks = {t.id: t for t in tasks}
    completed_task_ids = set()
    
    while remaining_tasks:
        # Find all tasks where dependencies are fully satisfied
        current_layer = []
        for task_id, task in list(remaining_tasks.items()):
            deps_satisfied = all(dep in completed_task_ids for dep in task.dependencies)
            if deps_satisfied:
                current_layer.append(task)
                
        if not current_layer:
            # Graph has unsortable cycles (should have been captured by validator.py)
            raise ValueError("Execution planner encountered cycle loop.")
            
        stages.append(current_layer)
        for task in current_layer:
            completed_task_ids.add(task.id)
            del remaining_tasks[task.id]
            
    return ExecutionPlan(
        id=f"plan_{uuid.uuid4().hex[:8]}",
        pipelineId=pipeline_data.get("id", "pipeline_unknown"),
        stages=stages,
        variables=pipeline_data.get("variables", {})
    )
"""
with open(f"{compiler_base}/planner.py", "w") as f:
    f.write(planner_py)

print("Scaffolding compiler pipeline successfully!")
