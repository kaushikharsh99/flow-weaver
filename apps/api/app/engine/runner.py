import time
import datetime
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from app import models
from app.engine.base import BaseNode, ExecutionContext
from app.engine.nodes.loaders import LoadCSVNode, LoadJSONNode
from app.engine.nodes.filters import FilterRowsNode
from app.engine.nodes.exports import WriteCSVNode
from app.engine.nodes.fallback import FallbackNode

def get_node_executor(type_id: str) -> BaseNode:
    """Factory to return executor instance for a given type_id."""
    if type_id == "load_csv":
        return LoadCSVNode()
    elif type_id == "load_json":
        return LoadJSONNode()
    elif type_id == "filter_rows":
        return FilterRowsNode()
    elif type_id == "write_csv":
        return WriteCSVNode()
    else:
        return FallbackNode(type_id)

def topological_sort(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[str]:
    """Perform Kahn's algorithm topological sort on the graph."""
    indegree = {n["id"]: 0 for n in nodes}
    adjacency = {n["id"]: [] for n in nodes}
    
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        if src in adjacency and tgt in indegree:
            adjacency[src].append(tgt)
            indegree[tgt] += 1
            
    # Find all nodes with 0 incoming edges
    queue = [node_id for node_id, degree in indegree.items() if degree == 0]
    sorted_order = []
    
    while queue:
        curr = queue.pop(0)
        sorted_order.append(curr)
        for neighbor in adjacency[curr]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
                
    if len(sorted_order) != len(nodes):
        raise ValueError("Pipeline contains cycles (Directed loops are not allowed).")
        
    return sorted_order

def execute_pipeline(execution_id: str, db_session: Session, ws_manager=None) -> None:
    """Sequential execution of a pipeline DAG."""
    import asyncio
    
    db = db_session
    execution = db.query(models.Execution).filter(models.Execution.id == execution_id).first()
    if not execution:
        return
        
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == execution.pipeline_id).first()
    if not pipeline:
        execution.status = "failed"
        db.commit()
        return

    # Helper to send dynamic ws alerts if server manager exists
    async def send_ws(event: Dict[str, Any]):
        if ws_manager:
            await ws_manager.send_event(execution_id, event)
            
    # Gather nodes and edges
    nodes = pipeline.nodes or []
    edges = pipeline.edges or []
    variables = pipeline.variables or {}
    
    # Exclude disabled and comment nodes from execution DAG
    active_nodes = [n for n in nodes if n.get("type") != "commentNode" and not n.get("data", {}).get("disabled", False)]
    active_node_ids = {n["id"] for n in active_nodes}
    active_edges = [e for e in edges if e["source"] in active_node_ids and e["target"] in active_node_ids]
    
    execution.status = "running"
    db.commit()
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(send_ws({
        "type": "EXECUTION_STARTED",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }))
    
    # Store outputs of intermediate nodes: maps node_id -> { port_id -> value }
    outputs_store: Dict[str, Dict[str, Any]] = {}
    
    try:
        order = topological_sort(active_nodes, active_edges)
        node_map = {n["id"]: n for n in active_nodes}
        total_steps = len(order)
        
        for idx, node_id in enumerate(order):
            # Check for cancellation
            db.refresh(execution)
            if execution.status == "cancelled":
                loop.run_until_complete(send_ws({
                    "type": "LOG",
                    "level": "warn",
                    "nodeId": node_id,
                    "message": "Execution cancelled by user. Terminating process."
                }))
                return
                
            node = node_map[node_id]
            node_data = node.get("data", {})
            type_id = node_data.get("typeId", "")
            title = node_data.get("title", type_id)
            params = node_data.get("params", {})
            
            loop.run_until_complete(send_ws({
                "type": "NODE_UPDATE",
                "nodeId": node_id,
                "status": "running",
                "progress": int((idx / total_steps) * 100)
            }))
            
            loop.run_until_complete(send_ws({
                "type": "LOG",
                "level": "info",
                "nodeId": node_id,
                "message": f"Running node '{title}' [{type_id}]"
            }))
            
            # Gathers inputs from upstream connected edges
            inputs = {}
            for edge in active_edges:
                if edge["target"] == node_id:
                    src_node = edge["source"]
                    src_port = edge["sourceHandle"]
                    target_port = edge["targetHandle"]
                    
                    if src_node in outputs_store and src_port in outputs_store[src_node]:
                        inputs[target_port] = outputs_store[src_node][src_port]
            
            # Execute node logic
            executor = get_node_executor(type_id)
            ctx = ExecutionContext(variables, params, inputs)
            
            try:
                start_time = time.perf_counter()
                outputs = executor.execute(ctx)
                end_time = time.perf_counter()
                
                # Store output results
                outputs_store[node_id] = outputs
                
                # Write logs to ws stream
                for log_msg in ctx.logs:
                    loop.run_until_complete(send_ws({
                        "type": "LOG",
                        "level": "info",
                        "nodeId": node_id,
                        "message": log_msg
                    }))
                    
                duration = round((end_time - start_time) * 1000)
                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "success",
                    "progress": int(((idx + 1) / total_steps) * 100),
                    # Provide a generic payload preview if applicable
                    "preview": outputs.get("out") if isinstance(outputs.get("out"), dict) else None
                }))
                
            except Exception as node_err:
                loop.run_until_complete(send_ws({
                    "type": "LOG",
                    "level": "error",
                    "nodeId": node_id,
                    "message": f"Execution failed on node '{title}': {str(node_err)}"
                }))
                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "error"
                }))
                raise node_err
                
        # Completed successfully
        execution.status = "completed"
        execution.progress = 100
        execution.completed_at = datetime.datetime.utcnow()
        db.commit()
        
        loop.run_until_complete(send_ws({
            "type": "EXECUTION_COMPLETED",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }))
        
    except Exception as err:
        execution.status = "failed"
        execution.completed_at = datetime.datetime.utcnow()
        db.commit()
        
        loop.run_until_complete(send_ws({
            "type": "EXECUTION_FAILED",
            "error": str(err),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }))
    finally:
        loop.close()
