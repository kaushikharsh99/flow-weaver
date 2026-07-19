import time
import datetime
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app import models

# Import Core SDK packages
from flowweaver.sdk import Node, Dataset, ExecutionContext

# Import compiler pipeline modules
from app.engine.compiler.validator import validate_pipeline
from app.engine.compiler.builder import build_tasks
from app.engine.compiler.optimizer import optimize_tasks
from app.engine.compiler.planner import generate_plan
from app.engine.registry import registry

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

    # Helper to send WS events
    async def send_ws(event: Dict[str, Any]):
        if ws_manager:
            await ws_manager.send_event(execution_id, event)
            
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
    
    # Gathers execution outputs mapping: node_id -> { port_id -> value }
    # Now, values inside port dictionary are Dataset wrappers!
    outputs_store: Dict[str, Dict[str, Any]] = {}
    
    try:
        pipeline_dict = {
            "id": pipeline.id,
            "nodes": nodes,
            "edges": edges,
            "variables": variables,
            "settings": pipeline.settings or {}
        }
        
        # 1. Compile stages
        loop.run_until_complete(send_ws({"type": "LOG", "level": "info", "message": "Starting compiler validation checks..."}))
        val_res = validate_pipeline(pipeline_dict)
        if not val_res.valid:
            err_msg = next((iss.message for iss in val_res.issues if iss.level == "error"), "Validation failed")
            raise ValueError(f"Compiler Validation Error: {err_msg}")
            
        for issue in val_res.issues:
            if issue.level == "warning":
                loop.run_until_complete(send_ws({"type": "LOG", "level": "warn", "nodeId": issue.node_id, "message": issue.message}))

        loop.run_until_complete(send_ws({"type": "LOG", "level": "info", "message": "Building logical execution DAG..."}))
        tasks = build_tasks(pipeline_dict)
        
        loop.run_until_complete(send_ws({"type": "LOG", "level": "info", "message": "Running graph optimizations..."}))
        optimized_tasks = optimize_tasks(tasks, pipeline_dict)
        
        loop.run_until_complete(send_ws({"type": "LOG", "level": "info", "message": "Generating concurrent execution scheduler plan..."}))
        plan = generate_plan(optimized_tasks, pipeline_dict)
        
        total_tasks = sum(len(stage) for stage in plan.stages)
        tasks_completed = 0
        
        loop.run_until_complete(send_ws({
            "type": "LOG", 
            "level": "info", 
            "message": f"Execution plan generated. Total stages: {len(plan.stages)}, Total tasks: {total_tasks}."
        }))

        # 2. Execute plan
        for stage_idx, stage in enumerate(plan.stages):
            loop.run_until_complete(send_ws({
                "type": "LOG",
                "level": "info",
                "message": f"Starting execution stage {stage_idx + 1}/{len(plan.stages)} ({len(stage)} task(s))"
            }))
            
            for task in stage:
                node_id = task.id
                
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
                title = node_id
                
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
                    "message": f"Running task '{title}' [{type_id}]"
                }))

                # Gather inputs from upstream outputs
                inputs = {}
                for tgt_port, src_info in task.inputs.items():
                    src_node = src_info["source_node"]
                    src_port = src_info["source_port"]
                    if src_node in outputs_store and src_port in outputs_store[src_node]:
                        inputs[tgt_port] = outputs_store[src_node][src_port]

                # Check cache checkpoint optimization
                if task.is_cached:
                    loop.run_until_complete(send_ws({
                        "type": "LOG",
                        "level": "info",
                        "nodeId": node_id,
                        "message": "Reusing cached checkpoint output for node."
                    }))
                    # Default mock caching
                    from flowweaver.sdk import TabularDataset
                    outputs = {"out": TabularDataset([{"cached": True}], columns=["cached"])}
                else:
                    executor = registry.get(type_id)
                    if not executor:
                        raise ValueError(f"No node executor found in registry for type: {type_id}")
                        
                    ctx = ExecutionContext(variables, params)
                    
                    try:
                        start_time = time.perf_counter()
                        outputs = executor.execute(inputs, ctx)
                        end_time = time.perf_counter()
                        
                        # Emit logged metrics and trace logs
                        for log_entry in ctx.logger.logs:
                            loop.run_until_complete(send_ws({
                                "type": "LOG",
                                "level": "info",
                                "nodeId": node_id,
                                "message": log_entry
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

                # Generate dynamic edge/node data preview from dataset abstraction!
                out_val = outputs.get("out")
                preview = None
                if isinstance(out_val, Dataset):
                    preview = {
                        "kind": "tabular",
                        "columns": out_val.columns(),
                        "rows": out_val.to_list()[:5], # Send top 5 rows sample to frontend
                        "stats": {
                            "rowCount": out_val.row_count(),
                            "columnCount": len(out_val.columns())
                        }
                    }

                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "success",
                    "progress": int((tasks_completed / total_tasks) * 100),
                    "preview": preview
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
