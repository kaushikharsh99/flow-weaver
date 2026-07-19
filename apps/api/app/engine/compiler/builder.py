from typing import Dict, Any, List
from app.engine.compiler.models import Task

def build_tasks(pipeline_data: Dict[str, Any]) -> List[Task]:
    """Convert nodes & edges into intermediate logical Tasks with explicit dependency listings."""
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
