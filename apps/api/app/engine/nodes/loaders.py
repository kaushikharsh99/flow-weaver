import csv
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
            {"label": "Comma", "value": ","}, {"label": "Tab", "value": "\t"}, {"label": "Semicolon", "value": ";"}
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
