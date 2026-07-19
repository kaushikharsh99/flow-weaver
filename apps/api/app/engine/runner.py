import time
import datetime
import asyncio
import threading
import resource
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

# Thread synchronization events for debugger pauses
# Maps execution_id -> threading.Event
resume_events: Dict[str, threading.Event] = {}

def get_memory_use() -> int:
    """Returns resident set size (RSS) memory in bytes on Linux."""
    try:
        # ru_maxrss is in KiB on Linux
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:
        return 0

def format_execution_error(err: Exception, node_label: str, inputs: Dict[str, Any]) -> str:
    """Format execution exceptions into friendly, actionable descriptions for researchers."""
    problem = str(err)
    suggestion = "Verify that parameters and connections are correct."
    available_cols_msg = ""
    
    if isinstance(err, KeyError):
        key_name = str(err).strip("'")
        problem = f"Column '{key_name}' not found in the input dataset."
        suggestion = "Update the parameter in the Inspector to select one of the available columns."
        # Gather available columns from input datasets
        cols = []
        for port_id, dataset in inputs.items():
            if hasattr(dataset, "columns") and callable(dataset.columns):
                cols.extend(dataset.columns())
        if cols:
            available_cols_msg = "\nAvailable columns:\n" + "\n".join(f"- {col}" for col in sorted(list(set(cols))))
            
    elif isinstance(err, FileNotFoundError):
        problem = f"File not found: {str(err)}"
        suggestion = "Verify the file path exists and is accessible. Ensure relative paths are correct."
        
    elif "re.error" in str(type(err)) or "invalid regex" in str(err).lower():
        problem = f"Invalid regular expression compilation failed: {str(err)}"
        suggestion = "Check regex syntax syntax (e.g. escaping, braces, wildcards)."

    formatted = f"""Node: {node_label}

Problem:
{problem}
{available_cols_msg}

Suggestion:
{suggestion}"""
    return formatted

def execute_pipeline(execution_id: str, db_session: Session, ws_manager=None) -> None:
    """Sequential execution of a compiled pipeline execution plan supporting debugger breakpoints."""
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
    
    # Initialize thread event for resume triggers
    resume_event = threading.Event()
    resume_events[execution_id] = resume_event
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(send_ws({
        "type": "EXECUTION_STARTED",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }))
    
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
                title = node_id
                
                orig_node = next((n for n in nodes if n.get("id") == node_id), None)
                if orig_node:
                    title = orig_node.get("data", {}).get("title", type_id)

                # --- Pipeline Debugger Breakpoint Logic ---
                is_breakpoint = params.get("__breakpoint__") is True
                if is_breakpoint or execution.status == "paused":
                    execution.status = "paused"
                    db.commit()
                    
                    loop.run_until_complete(send_ws({
                        "type": "NODE_UPDATE",
                        "nodeId": node_id,
                        "status": "paused",
                        "progress": int((tasks_completed / total_tasks) * 100),
                        "message": f"Pipeline execution paused at breakpoint on node '{title}'."
                    }))
                    loop.run_until_complete(send_ws({
                        "type": "LOG",
                        "level": "warn",
                        "nodeId": node_id,
                        "message": f"Breakpoint hit on '{title}'. Waiting for debugger resume signal..."
                    }))
                    
                    # Lock and wait for resume event
                    resume_event.clear()
                    resume_event.wait()
                    
                    # Recheck cancellation or restart state after wake
                    db.refresh(execution)
                    if execution.status == "cancelled":
                        return
                    
                    # Set execution back to running
                    execution.status = "running"
                    db.commit()
                    
                    loop.run_until_complete(send_ws({
                        "type": "LOG",
                        "level": "info",
                        "nodeId": node_id,
                        "message": f"Debugger signal received. Resuming execution from '{title}'."
                    }))

                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "running",
                    "progress": int((tasks_completed / total_tasks) * 100)
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
                    from flowweaver.sdk import TabularDataset
                    outputs = {"out": TabularDataset([{"cached": True}], columns=["cached"])}
                    duration_ms = 0
                    mem_allocated = 0
                    rows_per_sec = 0.0
                else:
                    executor = registry.get(type_id)
                    if not executor:
                        raise ValueError(f"No node executor found in registry for type: {type_id}")
                        
                    ctx = ExecutionContext(variables, params)
                    
                    # Sync progress and cancellation callbacks (Phase 3 progress/cancellation hooks)
                    def progress_hook(pct, msg=None):
                        loop.run_until_complete(send_ws({
                            "type": "NODE_UPDATE",
                            "nodeId": node_id,
                            "status": "running",
                            "nodeProgress": pct,
                            "message": msg or f"Progress: {pct}%"
                        }))
                    ctx._progress_callback = progress_hook
                    
                    def cancel_hook():
                        db.refresh(execution)
                        return execution.status == "cancelled"
                    ctx._cancel_check = cancel_hook
                    
                    try:
                        start_time = time.perf_counter()
                        start_mem = get_memory_use()
                        
                        outputs = executor.execute(inputs, ctx)
                        
                        end_mem = get_memory_use()
                        end_time = time.perf_counter()
                        
                        # Calculate performance profiles
                        duration_ms = int((end_time - start_time) * 1000)
                        mem_allocated = max(0, end_mem - start_mem)
                        
                        # Calculate rows throughput
                        row_count = 0
                        out_val = outputs.get("out")
                        if isinstance(out_val, Dataset):
                            row_count = out_val.row_count() or 0
                            
                        rows_per_sec = round((row_count / (duration_ms / 1000.0)), 2) if duration_ms > 0 else 0.0
                        
                        # Ship intermediate user context logs
                        for log_entry in ctx.logger.logs:
                            loop.run_until_complete(send_ws({
                                "type": "LOG",
                                "level": "info",
                                "nodeId": node_id,
                                "message": log_entry
                            }))
                            
                        # Pretty stage throughput logs (Phase 3 Log system)
                        input_rows = sum(v.row_count() for v in inputs.values() if isinstance(v, Dataset) and v.row_count() is not None)
                        output_rows = out_val.row_count() if (isinstance(out_val, Dataset) and out_val.row_count() is not None) else None
                        
                        if isinstance(out_val, Dataset) and output_rows is not None:
                            is_filter_or_dedup = "filter" in category.lower() or "dedup" in category.lower() or "filter" in type_id.lower() or "dedup" in type_id.lower()
                            if is_filter_or_dedup and input_rows > 0:
                                diff = input_rows - output_rows
                                stage_msg = f"Deduplicated/Filtered: Removed {diff:,} rows ({output_rows:,} rows remaining)"
                            else:
                                stage_msg = f"Processed: ✓ {output_rows:,} row(s) completed"
                        else:
                            stage_msg = "✓ Node completed successfully."
                            
                        loop.run_until_complete(send_ws({
                            "type": "LOG",
                            "level": "info",
                            "nodeId": node_id,
                            "message": stage_msg
                        }))
                            
                    except Exception as node_err:
                        # Friendly Actionable Error Formatters (Phase 3 Error system)
                        formatted_err = format_execution_error(node_err, title, inputs)
                        loop.run_until_complete(send_ws({
                            "type": "LOG",
                            "level": "error",
                            "nodeId": node_id,
                            "message": formatted_err
                        }))
                        loop.run_until_complete(send_ws({
                            "type": "NODE_UPDATE",
                            "nodeId": node_id,
                            "status": "error"
                        }))
                        raise ValueError(formatted_err)
                
                # Cache output data results
                outputs_store[node_id] = outputs
                tasks_completed += 1
 
                # Generate dynamic edge data preview with schemas (Phase 3 Preview system)
                out_val = outputs.get("out")
                preview = None
                if isinstance(out_val, Dataset):
                    sample_rows = out_val.to_list()[:5]
                    inferred_schema = {}
                    if sample_rows:
                        for col in out_val.columns():
                            val = sample_rows[0].get(col)
                            inferred_schema[col] = type(val).__name__ if val is not None else "unknown"
                    else:
                        for col in out_val.columns():
                            inferred_schema[col] = "unknown"
                            
                    preview = {
                        "kind": "tabular",
                        "columns": out_val.columns(),
                        "rows": sample_rows,
                        "stats": {
                            "rowCount": out_val.row_count(),
                            "columnCount": len(out_val.columns()),
                            "schema": inferred_schema
                        }
                    }
 
                # Emit NODE_UPDATE with full profile metrics!
                loop.run_until_complete(send_ws({
                    "type": "NODE_UPDATE",
                    "nodeId": node_id,
                    "status": "success",
                    "progress": int((tasks_completed / total_tasks) * 100),
                    "preview": preview,
                    "metrics": {
                        "durationMs": duration_ms,
                        "memoryBytes": mem_allocated,
                        "rowsPerSec": rows_per_sec
                    }
                }))

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
        resume_events.pop(execution_id, None)
        loop.close()
