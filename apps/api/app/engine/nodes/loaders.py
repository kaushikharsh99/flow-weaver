import csv
import json
import os
from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext, TabularDataset
from app.engine.nodes.core_logic import load_jsonl_file, load_parquet_file, load_hf_hub_dataset

@node(name="Load CSV", category="Loaders", icon="FileSpreadsheet", description="Read a CSV file from path")
class LoadCSVNode(Node):
    id = "load_csv"
    out = Output.tabular(label="Rows")
    
    path = Param.file(label="File path", default="data/sample.csv", accept=".csv")
    delimiter = Param.select(label="Delimiter", default=",", options=[
        {"label": "Comma", "value": ","}, {"label": "Tab", "value": "\t"}, {"label": "Semicolon", "value": ";"}
    ])
    header = Param.boolean(label="Has header row", default=True)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        # Resolve env variables
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
            
        ctx.log(f"Loading CSV from: {path}")
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
                    return {"out": TabularDataset([], columns=[])}
            for row in reader:
                if has_header:
                    rows.append(dict(zip(header, row)))
                else:
                    rows.append({f"col_{i}": v for i, v in enumerate(row)})
        return {"out": TabularDataset(rows, columns=header if has_header else [])}


@node(name="Load JSON", category="Loaders", icon="FileText", description="Parse a JSON array of records")
class LoadJSONNode(Node):
    id = "load_json"
    out = Output.tabular(label="Records")
    
    path = Param.file(label="File path", default="data/sample.json", accept=".json")
    root_key = Param.text(label="Root key", default="", placeholder="data")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
            
        ctx.log(f"Loading JSON from: {path}")
        with open(path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            
        root = ctx.parameters.get("root_key", "")
        if root and isinstance(data, dict):
            data = data.get(root, data)
            
        if not isinstance(data, list):
            data = [data]
        return {"out": TabularDataset(data)}


@node(name="Load JSONL", category="Loaders", icon="Layers", description="Parse a JSON Lines file (one record per line)")
class LoadJSONLNode(Node):
    id = "load_jsonl"
    out = Output.tabular(label="Records")
    path = Param.file(label="File path", default="data/sample.jsonl", accept=".jsonl")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
        return {"out": load_jsonl_file(path)}


@node(name="Load Parquet", category="Loaders", icon="Database", description="Load Parquet dataset using Polars")
class LoadParquetNode(Node):
    id = "load_parquet"
    out = Output.tabular(label="Table")
    path = Param.file(label="File path", default="data/sample.parquet", accept=".parquet")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
        return {"out": load_parquet_file(path)}


@node(name="HuggingFace Dataset", category="Loaders", icon="Globe", description="Download a dataset from Hugging Face Hub")
class LoadHFDatasetNode(Node):
    id = "load_hf_dataset"
    out = Output.tabular(label="Dataset")
    
    dataset_id = Param.text(label="Dataset Name", default="imdb", placeholder="e.g. wikitext, imdb")
    split = Param.text(label="Split", default="train")
    limit = Param.number(label="Row Limit", default=100, min=1)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset_id = ctx.parameters.get("dataset_id", "imdb")
        split = ctx.parameters.get("split", "train")
        limit = int(ctx.parameters.get("limit", 100))
        return {"out": load_hf_hub_dataset(dataset_id, split=split, limit=limit)}
