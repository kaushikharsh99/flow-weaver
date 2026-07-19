import csv
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
