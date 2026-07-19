import os

engine_base = "apps/api/app/engine"

# 1. Overwrite base.py to import/redirect from flowweaver.sdk
base_py = """# Redirect imports to flowweaver.sdk
from flowweaver.sdk import Node, ExecutionContext, Dataset, TabularDataset

# Keeping aliases for backwards compatibility
BaseNode = Node
"""
with open(f"{engine_base}/base.py", "w") as f:
    f.write(base_py)

# 2. Overwrite engine/nodes/loaders.py to use SDK and Dataset abstraction
loaders_py = """import csv
import json
import os
from typing import Dict, Any
from flowweaver.sdk import Node, ExecutionContext, TabularDataset, Port, Parameter

class LoadCSVNode(Node):
    id = "load_csv"
    label = "Load CSV"
    category = "Loaders"
    description = "Read a CSV file from a URL or path"
    icon = "FileSpreadsheet"
    color = "#4f86c6"
    inputs = []
    outputs = [Port(id="out", label="rows", type="tabular")]
    params_schema = [
        Parameter(key="path", label="File path", type="text", default="data/users.csv"),
        Parameter(key="delimiter", label="Delimiter", type="select", default=",", options=[
            {"label": "Comma", "value": ","}, {"label": "Tab", "value": "\\t"}, {"label": "Semicolon", "value": ";"}
        ]),
        Parameter(key="header", label="Has header row", type="boolean", default=True),
    ]

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
            
        ctx.log(f"Reading CSV file from: {path}")
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
                    ctx.log("CSV file is empty.")
                    return {"out": TabularDataset([], columns=[])}
                    
            for row in reader:
                # Store row as dictionary matching columns
                row_dict = {}
                for idx, col in enumerate(header):
                    if idx < len(row):
                        row_dict[col] = row[idx]
                rows.append(row_dict)
                
        ctx.log(f"Successfully loaded {len(rows)} rows from CSV.")
        return {"out": TabularDataset(rows, columns=header)}

class LoadJSONNode(Node):
    id = "load_json"
    label = "Load JSON"
    category = "Loaders"
    description = "Parse a JSON array of records"
    icon = "FileText"
    color = "#4f86c6"
    inputs = []
    outputs = [Port(id="out", label="records", type="tabular")]
    params_schema = [
        Parameter(key="path", label="File path", type="text", default="data/records.json"),
        Parameter(key="root", label="Root key", type="text", default="data", placeholder="data"),
    ]

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
            
        ctx.log(f"Reading JSON file from: {path}")
        if not os.path.exists(path):
            raise FileNotFoundError(f"JSON file not found at path: {path}")
            
        with open(path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            
        root_key = ctx.parameters.get("root", "")
        if root_key and isinstance(data, dict):
            data = data.get(root_key, data)
            
        if not isinstance(data, list):
            data = [data]
            
        ctx.log(f"Successfully parsed JSON data array.")
        return {"out": TabularDataset(data)}
"""
with open(f"{engine_base}/nodes/loaders.py", "w") as f:
    f.write(loaders_py)

# 3. Overwrite engine/nodes/filters.py to use SDK and Dataset abstraction
filters_py = """from typing import Dict, Any
from flowweaver.sdk import Node, ExecutionContext, TabularDataset, Port, Parameter

class FilterRowsNode(Node):
    id = "filter_rows"
    label = "Filter Rows"
    category = "Filters"
    description = "Keep rows matching a condition"
    icon = "Filter"
    color = "#c67a4f"
    inputs = [Port(id="in", label="rows", type="tabular", required=True)]
    outputs = [Port(id="out", label="rows", type="tabular")]
    params_schema = [
        Parameter(key="column", label="Column", type="text", default="age"),
        Parameter(key="op", label="Operator", type="select", default=">", options=[
            {"label": ">", "value": ">"}, {"label": "<", "value": "<"}, {"label": "=", "value": "="}, {"label": "!=", "value": "!="}
        ]),
        Parameter(key="value", label="Value", type="text", default="25"),
    ]

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in")
        if not dataset:
            ctx.log("Warning: Input dataset is empty.")
            return {"out": TabularDataset([], columns=[])}
            
        columns = dataset.columns()
        rows_dicts = dataset.to_list()
        
        col_name = ctx.parameters.get("column", "")
        operator = ctx.parameters.get("op", "=")
        filter_val = ctx.parameters.get("value", "")
        
        if col_name not in columns:
            ctx.log(f"Filter Column '{col_name}' not found. Returning original dataset.")
            return {"out": dataset}
            
        filtered_rows = []
        ctx.log(f"Filtering {len(rows_dicts)} rows on column '{col_name}' {operator} '{filter_val}'")
        
        for row in rows_dicts:
            cell_val = str(row.get(col_name, "")).strip()
            
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
                
        ctx.log(f"Filter completed. Retained {len(filtered_rows)} / {len(rows_dicts)} rows.")
        return {"out": TabularDataset(filtered_rows, columns=columns)}
"""
with open(f"{engine_base}/nodes/filters.py", "w") as f:
    f.write(filters_py)

# 4. Overwrite engine/nodes/exports.py to use SDK and Dataset abstraction
exports_py = """import csv
import os
from typing import Dict, Any
from flowweaver.sdk import Node, ExecutionContext, Port, Parameter

class WriteCSVNode(Node):
    id = "write_csv"
    label = "Write CSV"
    category = "Export"
    description = "Write rows to CSV file"
    icon = "Save"
    color = "#c6b74f"
    inputs = [Port(id="in", label="rows", type="tabular", required=True)]
    outputs = []
    params_schema = [
        Parameter(key="path", label="Output path", type="text", default="out/results.csv"),
        Parameter(key="compress", label="Gzip", type="boolean", default=False),
    ]

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in")
        if not dataset:
            ctx.log("Warning: Input dataset is empty. Skipping export.")
            return {}
            
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
            
        ctx.log(f"Writing dataset to CSV file: {path}")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        columns = dataset.columns()
        rows_dicts = dataset.to_list()
        
        with open(path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if columns:
                writer.writerow(columns)
            for row in rows_dicts:
                writer.writerow([row.get(col, "") for col in columns])
                
        ctx.log(f"Successfully wrote {len(rows_dicts)} rows to output CSV file.")
        return {}
"""
with open(f"{engine_base}/nodes/exports.py", "w") as f:
    f.write(exports_py)

# 5. Overwrite engine/nodes/fallback.py to use SDK and Dataset abstraction
fallback_py = """import time
import random
from typing import Dict, Any
from flowweaver.sdk import Node, ExecutionContext, TabularDataset

class FallbackNode(Node):
    def __init__(self, node_type_id: str):
        self.node_type_id = node_type_id
        self.id = node_type_id

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Executing fallback handler for dynamic node type '{self.node_type_id}'")
        
        # Simulate delay
        delay = 0.2 + random.random() * 0.4
        time.sleep(delay)
        
        # Provide some dummy outputs
        out_val = inputs.get("in", "Simulated Output")
        
        # Wrap string/list in TabularDataset if appropriate
        if isinstance(out_val, str):
            out_val = TabularDataset([{"text": out_val}], columns=["text"])
        elif isinstance(out_val, list):
            out_val = TabularDataset([{"item": x} for x in out_val], columns=["item"])
            
        return {"out": out_val}
"""
with open(f"{engine_base}/nodes/fallback.py", "w") as f:
    f.write(fallback_py)

# 6. Overwrite engine/registry.py to import definitions from flowweaver.sdk
registry_py = """from typing import List, Dict, Any, Optional
from flowweaver.sdk import Node, Port, Parameter
from app.engine.nodes.loaders import LoadCSVNode, LoadJSONNode
from app.engine.nodes.filters import FilterRowsNode
from app.engine.nodes.exports import WriteCSVNode
from app.engine.nodes.fallback import FallbackNode

class NodeRegistry:
    def __init__(self):
        self._nodes: Dict[str, Node] = {}

    def register(self, node: Node):
        self._nodes[node.id] = node

    def get(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def list_all(self) -> List[Node]:
        return list(self._nodes.values())

    def validate_config(self, node_id: str, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        node = self.get(node_id)
        if not node:
            return False, [f"Node type '{node_id}' not found in registry."]
        
        errors = []
        # Validate parameters against schema
        for param in node.params_schema:
            val = config.get(param.key)
            if val is None:
                continue
                
            if param.type == "number" or param.type == "slider":
                if not isinstance(val, (int, float)):
                    errors.append(f"Parameter '{param.key}' must be a number.")
                else:
                    if param.min is not None and val < param.min:
                        errors.append(f"Parameter '{param.key}' must be >= {param.min}.")
                    if param.max is not None and val > param.max:
                        errors.append(f"Parameter '{param.key}' must be <= {param.max}.")
            elif param.type == "boolean":
                if not isinstance(val, bool):
                    errors.append(f"Parameter '{param.key}' must be a boolean.")
            elif param.type == "select":
                if param.options:
                    valid_values = {opt["value"] for opt in param.options}
                    if str(val) not in valid_values:
                        errors.append(f"Parameter '{param.key}' value '{val}' is not a valid option.")
                        
        return len(errors) == 0, errors

# Create global registry instance
registry = NodeRegistry()

# Register core implementations
registry.register(LoadCSVNode())
registry.register(LoadJSONNode())
registry.register(FilterRowsNode())
registry.register(WriteCSVNode())

# Seed fallback nodes to complete the 24 built-in list
fallback_node_ids = [
    ("http_fetch", "HTTP Fetch", "Loaders", "Fetch data from a REST endpoint", "Globe", "#4f86c6", [], [Port(id="out", label="response", type="any")]),
    ("load_sql", "SQL Query", "Loaders", "Run a SELECT against a database", "Database", "#4f86c6", [], [Port(id="out", label="rows", type="tabular")]),
    ("load_s3", "S3 Bucket", "Loaders", "List and read objects from S3", "Cloud", "#4f86c6", [], [Port(id="out", label="objects", type="any")]),
    ("load_images", "Load Images", "Loaders", "Read a directory of images", "ImageIcon", "#4f86c6", [], [Port(id="out", label="images", type="image")]),
    ("search_text", "Search Text", "Filters", "Regex/substring filter on a text column", "Search", "#c67a4f", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="matches", type="tabular")]),
    ("sample_rows", "Sample", "Filters", "Randomly sample N rows", "Shuffle", "#c67a4f", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("select_columns", "Select Columns", "Transform", "Project a subset of columns", "Columns3", "#7a4fc6", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("sort_rows", "Sort", "Transform", "Sort by a column", "ArrowUpDown", "#7a4fc6", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("join_rows", "Join", "Transform", "Join two tables on a key", "GitMerge", "#7a4fc6", [Port(id="left", label="left", type="tabular", required=True), Port(id="right", label="right", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("split_col", "Split Column", "Transform", "Split a column by a delimiter", "Scissors", "#7a4fc6", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("map_expr", "Map Expression", "Transform", "Compute a new column from an expression", "Wand2", "#7a4fc6", [Port(id="in", label="rows", type="any", required=True)], [Port(id="out", label="rows", type="any")]),
    ("dedup_exact", "Dedup Exact", "Dedup", "Remove exact duplicate rows", "Copy", "#4fc6a0", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("dedup_fuzzy", "Dedup Fuzzy", "Dedup", "Fuzzy-match near duplicates", "Fingerprint", "#4fc6a0", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("normalize", "Normalize", "Dedup", "Normalize whitespace, case, encoding", "SlidersHorizontal", "#4fc6a0", [Port(id="in", label="rows", type="any", required=True)], [Port(id="out", label="rows", type="any")]),
    ("tokenize", "Tokenize", "NLP", "Split text into tokens", "Type", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="tokens", type="any")]),
    ("detect_lang", "Detect Language", "NLP", "Identify text language", "Languages", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="text+lang", type="text")]),
    ("sentiment", "Sentiment", "NLP", "Classify text sentiment", "Sparkles", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="labeled", type="text")]),
    ("embed_text", "Embeddings", "NLP", "Content vector embeddings", "Hash", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="vectors", type="any")]),
    ("summarize", "Summarize", "NLP", "Abstractive summarization", "MessageSquare", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="summaries", type="text")]),
    ("write_json", "Write JSON", "Export", "Serialize records to JSON", "Download", "#c6b74f", [Port(id="in", label="rows", type="any", required=True)], []),
    ("webhook", "Send Webhook", "Export", "POST rows to an endpoint", "Send", "#c6b74f", [Port(id="in", label="rows", type="any", required=True)], []),
    ("upload_s3", "Upload S3", "Export", "Upload files to S3", "Upload", "#c6b74f", [Port(id="in", label="data", type="any", required=True)], []),
]

for node_id, label, cat, desc, icon, color, inputs, outputs in fallback_node_ids:
    fallback_node = FallbackNode(node_id)
    fallback_node.label = label
    fallback_node.category = cat
    fallback_node.description = desc
    fallback_node.icon = icon
    fallback_node.color = color
    fallback_node.inputs = inputs
    fallback_node.outputs = outputs
    fallback_node.params_schema = []
    registry.register(fallback_node)
"""
with open(f"{engine_base}/registry.py", "w") as f:
    f.write(registry_py)

# 7. Overwrite engine/runner.py to execute utilizing SDK node execution signature and Dataset previews
runner_py = """import time
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
    \"\"\"Sequential execution of a compiled pipeline execution plan.\"\"\"
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
"""
with open(f"{engine_base}/runner.py", "w") as f:
    f.write(runner_py)

print("SDK refactoring completed successfully!")
