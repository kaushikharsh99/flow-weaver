from typing import Dict, Any
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
