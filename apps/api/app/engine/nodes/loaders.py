import csv
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
