from typing import List, Dict, Any
from app.engine.compiler.models import ValidationResult, ValidationError
from app.engine.registry import registry

def validate_pipeline(pipeline_data: Dict[str, Any]) -> ValidationResult:
    """Run comprehensive semantic validation checks on the pipeline DAG."""
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
