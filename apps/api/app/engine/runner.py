import time
import datetime
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app import models

# Import base node executor interface and fallback definition
from app.engine.base import BaseNode, ExecutionContext
from app.engine.nodes.loaders import LoadCSVNode, LoadJSONNode
from app.engine.nodes.filters import FilterRowsNode
from app.engine.nodes.exports import WriteCSVNode
from app.engine.nodes.fallback import FallbackNode

# Import compiler pipeline modules
from app.engine.compiler.validator import validate_pipeline
from app.engine.compiler.builder import build_tasks
from app.engine.compiler.optimizer import optimize_tasks
from app.engine.compiler.planner import generate_plan

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

def execute_pipeline(execution_id: str, db_session: Session, ws_manager=None) -> None:
    """Sequential execution of a compiled pipeline execution plan."""
    db = db_session
    execution = db.query(models.Execution).filter(models.Execution.id == execution_id).first()
    if not execution:
        return
        
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == execution.pipeline_id).first()
    if not pipeline:
        execution.status = "failed"
        db.commit()
        return

    # Helper to send live WS events
    async def send_ws(event: Dict[str, Any]):
        if ws_manager:
            await ws_manager.send_event(execution_id, event)
            
    # Gather nodes and edges
    nodes = pipeline.nodes or []
    edges = pipeline.edges or []
    variables = pipeline.variables or {}
    
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
        # Prepare compilation context dictionary
        pipeline_dict = {
            "id": pipeline.id,
            "nodes": nodes,
            "edges": edges,
            "variables": variables,
            "settings": pipeline.settings or {}
        }
        
        # 1. Compile Pipeline Stage: Semantic Validation
        loop.run_until_complete(send_ws({
            "type": "LOG",
            "level": "info",
            "message": "Starting compiler validation checks..."
        }))
        val_res = validate_pipeline(pipeline_dict)
        if not val_res.valid:
            err_msg = next((iss.message for iss in val_res.issues if iss.level == "error"), "Validation failed")
            raise ValueError(f"Compiler Validation Error: {err_msg}")
            
        # Write warnings if any
        for issue in val_res.issues:
            if issue.level == "warning":
                loop.run_until_complete(send_ws({
                    "type": "LOG",
                    "level": "warn",
                    "nodeId": issue.node_id,
                    "message": issue.message
                }))

        # 2. Compile Pipeline Stage: Graph Building
        loop.run_until_complete(send_ws({
            "type": "LOG",
            "level": "info",
            "message": "Building logical execution DAG..."
        }))
        tasks = build_tasks(pipeline_dict)
        
        # 3. Compile Pipeline Stage: Graph Optimization
        loop.run_until_complete(send_ws({
            "type": "LOG",
            "level": "info",
            "message": "Running graph optimizations..."
        }))
        optimized_tasks = optimize_tasks(tasks, pipeline_dict)
        
        # 4. Compile Pipeline Stage: Execution Planning & Scheduling
        loop.run_until_complete(send_ws({
            "type": "LOG",
            "level": "info",
            "message": "Generating concurrent execution scheduler plan..."
        }))
        plan = generate_plan(optimized_tasks, pipeline_dict)
        
        # Count total active tasks for progress tracking
        total_tasks = sum(len(stage) for stage in plan.stages)
        tasks_completed = 0
        
        loop.run_until_complete(send_ws({
            "type": "LOG",
            "level": "info",
            "message": f"Compiled execution plan generated successfully. Found {len(plan.stages)} stage(s) with {total_tasks} task(s)."
        }))

        # 5. Core Execution Loop: Execute Stage by Stage
        for stage_idx, stage in enumerate(plan.stages):
            loop.run_until_complete(send_ws({
                "type": "LOG",
                "level": "info",
                "message": f"Starting execution stage {stage_idx + 1}/{len(plan.stages)} ({len(stage)} task(s))"
            }))
            
            # Note: For now, we execute tasks within a stage sequentially to satisfy Milestone 1.
            # In Phase 3/Milestone 3, we will spin off these tasks into parallel threads/workers.
            for task in stage:
                node_id = task.id
                
                # Check for user cancellation
                db.refresh(execution)
                if execution.status == "cancelled":
                    loop.run_until_complete(send_ws({
                        "type": "LOG",
                        "level": "warn",
                        "nodeId": node_id,
                        "message": "Execution cancelled by user. Terminating plan execution."
                    }))
                    return
                
                type_id = task.type_id
                params = task.parameters
                title = node_id  # default title fallback
                
                # Fetch node title from original config if available
                orig_node = next((n for n in nodes if n.get("id") == node_id), None)
                if orig_node:
                    title = orig_node.get("data", {}).get("title", type_id)

                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "running",
                    "progress": int((tasks_completed / total_tasks) * 100)
                }))

                loop.run_until_complete(send_ws({
                    "type": "LOG",
                    "level": "info",
                    "nodeId": node_id,
                    "message": f"Running node: '{title}' [{type_id}]"
                }))

                # Gather connections mapped by inputs
                inputs = {}
                for tgt_port, src_info in task.inputs.items():
                    src_node = src_info["source_node"]
                    src_port = src_info["source_port"]
                    if src_node in outputs_store and src_port in outputs_store[src_node]:
                        inputs[tgt_port] = outputs_store[src_node][src_port]

                # Check if task output is cached
                if task.is_cached:
                    loop.run_until_complete(send_ws({
                        "type": "LOG",
                        "level": "info",
                        "nodeId": node_id,
                        "message": "Reusing cached checkpoint output for node."
                    }))
                    # Mock cached retrieval (in production, loaded from SQLite / File System cache index)
                    outputs = {"out": "Cached Checkpoint Value"}
                else:
                    executor = get_node_executor(type_id)
                    ctx = ExecutionContext(variables, params, inputs)
                    
                    try:
                        start_time = time.perf_counter()
                        outputs = executor.execute(ctx)
                        end_time = time.perf_counter()
                        
                        # Emit logged entries from this task execution
                        for log_msg in ctx.logs:
                            loop.run_until_complete(send_ws({
                                "type": "LOG",
                                "level": "info",
                                "nodeId": node_id,
                                "message": log_msg
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
                
                # Cache output data results
                outputs_store[node_id] = outputs
                tasks_completed += 1

                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "success",
                    "progress": int((tasks_completed / total_tasks) * 100),
                    "preview": outputs.get("out") if isinstance(outputs.get("out"), dict) else None
                }))

        # Completed all stages successfully
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
