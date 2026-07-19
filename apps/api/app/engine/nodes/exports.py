import csv
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
