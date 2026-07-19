from typing import Dict, Any
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
