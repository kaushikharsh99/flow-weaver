import os

# Base directory for the backend engine
engine_base = "apps/api/app/engine"
os.makedirs(f"{engine_base}/nodes", exist_ok=True)

# 1. Write base.py
base_py = """import abc
from typing import Dict, Any, List

class ExecutionContext:
    def __init__(self, variables: Dict[str, Any], parameters: Dict[str, Any], inputs: Dict[str, Any]):
        self.variables = variables
        self.parameters = parameters
        self.inputs = inputs  # Maps: input_port_id -> value
        self.logs: List[str] = []

    def log(self, message: str):
        self.logs.append(message)

class BaseNode(abc.ABC):
    @abc.abstractmethod
    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        \"\"\"
        Execute the node logic.
        Returns a dictionary mapping: output_port_id -> value.
        \"\"\"
        pass
"""

with open(f"{engine_base}/base.py", "w") as f:
    f.write(base_py)

# 2. Write loaders.py
loaders_py = """import csv
import json
import os
from typing import Dict, Any
from app.engine.base import BaseNode, ExecutionContext

class LoadCSVNode(BaseNode):
    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        # Resolve variables in path like ${BASE_DIR}/file.csv
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v))
            path = path.replace(f"${k}", str(v))
            
        ctx.log(f"Reading CSV file from path: {path}")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found at path: {path}")
            
        delimiter = ctx.parameters.get("delimiter", ",")
        has_header = ctx.parameters.get("header", True)
        
        rows = []
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = []
            if has_header:
                try:
                    header = next(reader)
                except StopIteration:
                    ctx.log("Warning: CSV file is empty.")
                    return {"out": {"columns": [], "rows": []}}
                    
            for row in reader:
                rows.append(row)
                
        ctx.log(f"Successfully loaded {len(rows)} rows from CSV.")
        return {
            "out": {
                "columns": header,
                "rows": rows
            }
        }

class LoadJSONNode(BaseNode):
    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v))
            path = path.replace(f"${k}", str(v))
            
        ctx.log(f"Reading JSON file from path: {path}")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"JSON file not found at path: {path}")
            
        with open(path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Optional root key selection
        root_key = ctx.parameters.get("root", "")
        if root_key and isinstance(data, dict):
            data = data.get(root_key, data)
            
        ctx.log(f"Successfully parsed JSON data object.")
        return {"out": data}
"""

with open(f"{engine_base}/nodes/loaders.py", "w") as f:
    f.write(loaders_py)

# 3. Write filters.py
filters_py = """from typing import Dict, Any
from app.engine.base import BaseNode, ExecutionContext

class FilterRowsNode(BaseNode):
    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        data = ctx.inputs.get("in")
        if not data or not isinstance(data, dict) or "rows" not in data:
            ctx.log("Warning: Input data is empty or invalid shape.")
            return {"out": {"columns": [], "rows": []}}
            
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        
        col_name = ctx.parameters.get("column", "")
        operator = ctx.parameters.get("op", "=")
        filter_val = ctx.parameters.get("value", "")
        
        if col_name not in columns:
            ctx.log(f"Filter Column '{col_name}' not found. Returning original rows.")
            return {"out": data}
            
        col_idx = columns.index(col_name)
        filtered_rows = []
        
        ctx.log(f"Filtering {len(rows)} rows on column '{col_name}' {operator} '{filter_val}'")
        
        for row in rows:
            if col_idx >= len(row):
                continue
            cell_val = str(row[col_idx]).strip()
            
            # Match operator
            match = False
            if operator == "=":
                match = cell_val == str(filter_val).strip()
            elif operator == "!=":
                match = cell_val != str(filter_val).strip()
            elif operator == ">":
                try:
                    match = float(cell_val) > float(filter_val)
                except ValueError:
                    match = cell_val > str(filter_val)
            elif operator == "<":
                try:
                    match = float(cell_val) < float(filter_val)
                except ValueError:
                    match = cell_val < str(filter_val)
                    
            if match:
                filtered_rows.append(row)
                
        ctx.log(f"Filter completed. Retained {len(filtered_rows)} / {len(rows)} rows.")
        return {
            "out": {
                "columns": columns,
                "rows": filtered_rows
            }
        }
"""

with open(f"{engine_base}/nodes/filters.py", "w") as f:
    f.write(filters_py)

# 4. Write exports.py
exports_py = """import csv
import os
from typing import Dict, Any
from app.engine.base import BaseNode, ExecutionContext

class WriteCSVNode(BaseNode):
    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        data = ctx.inputs.get("in")
        if not data or not isinstance(data, dict) or "rows" not in data:
            ctx.log("Warning: Input data is empty or invalid. Skipping export.")
            return {}
            
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v))
            path = path.replace(f"${k}", str(v))
            
        ctx.log(f"Writing dataset to CSV file at: {path}")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        
        with open(path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if columns:
                writer.writerow(columns)
            writer.writerows(rows)
            
        ctx.log(f"Successfully wrote {len(rows)} rows to output CSV file.")
        return {}
"""

with open(f"{engine_base}/nodes/exports.py", "w") as f:
    f.write(exports_py)

# 5. Write fallback.py
fallback_py = """import time
import random
from typing import Dict, Any
from app.engine.base import BaseNode, ExecutionContext

class FallbackNode(BaseNode):
    def __init__(self, node_type_id: str):
        self.node_type_id = node_type_id

    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Executing fallback simulated handler for node type '{self.node_type_id}'")
        
        # Simulate delay
        delay = 0.3 + random.random() * 0.6
        time.sleep(delay)
        
        # Provide some dummy outputs based on node type
        outputs = {}
        if self.node_type_id == "sentiment":
            outputs["out"] = {"sentiment": "positive", "confidence": 0.94}
        elif self.node_type_id == "tokenize":
            outputs["out"] = ["simulated", "tokenized", "output"]
        else:
            outputs["out"] = ctx.inputs.get("in", "Simulated Output")
            
        return outputs
"""

with open(f"{engine_base}/nodes/fallback.py", "w") as f:
    f.write(fallback_py)

# 6. Write runner.py
runner_py = """import time
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
    \"\"\"Factory to return executor instance for a given type_id.\"\"\"
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
    \"\"\"Perform Kahn's algorithm topological sort on the graph.\"\"\"
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
    \"\"\"Sequential execution of a pipeline DAG.\"\"\"
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
"""

with open(f"{engine_base}/runner.py", "w") as f:
    f.write(runner_py)

print("Scaffolding execution engine completed successfully!")
