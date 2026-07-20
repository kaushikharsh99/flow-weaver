from typing import Dict, Any
from flowweaver.sdk import Node, Output, Param, node, ExecutionContext
from flowweaver.std import io


@node(name="Load CSV", category="Loaders", icon="FileSpreadsheet", description="Read a CSV file from path")
class LoadCSVNode(Node):
    id = "load_csv"
    out = Output.tabular(label="Rows")
    
    path = Param.file(label="File path", default="data/sample.csv", accept=".csv")
    delimiter = Param.select(label="Delimiter", default=",", options=[
        {"label": "Comma", "value": ","}, {"label": "Tab", "value": "\t"}, {"label": "Semicolon", "value": ";"}
    ])

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "data/sample.csv")
        delim = ctx.current_params.get("delimiter", ",")
        return ctx.call("flowweaver.std.io.import_dataset", path=path, delimiter=delim)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "data/sample.csv")
        delim = ctx.parameters.get("delimiter", ",")
        return {"out": io.import_dataset(path, delimiter=delim)}


@node(name="Load JSON", category="Loaders", icon="FileText", description="Parse a JSON array of records")
class LoadJSONNode(Node):
    id = "load_json"
    out = Output.tabular(label="Records")
    
    path = Param.file(label="File path", default="data/sample.json", accept=".json")
    root_key = Param.text(label="Root key", default="", placeholder="data")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "data/sample.json")
        root = ctx.current_params.get("root_key", "")
        return ctx.call("flowweaver.std.io.import_dataset", path=path, root_key=root)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "data/sample.json")
        root = ctx.parameters.get("root_key", "")
        return {"out": io.import_dataset(path, root_key=root)}


@node(name="Load JSONL", category="Loaders", icon="Layers", description="Parse a JSON Lines file (one record per line)")
class LoadJSONLNode(Node):
    id = "load_jsonl"
    out = Output.tabular(label="Records")
    path = Param.file(label="File path", default="data/sample.jsonl", accept=".jsonl")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "data/sample.jsonl")
        return ctx.call("flowweaver.std.io.import_dataset", path=path)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "data/sample.jsonl")
        return {"out": io.import_dataset(path)}


@node(name="Load Parquet", category="Loaders", icon="Database", description="Load Parquet dataset")
class LoadParquetNode(Node):
    id = "load_parquet"
    out = Output.tabular(label="Table")
    path = Param.file(label="File path", default="data/sample.parquet", accept=".parquet")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "data/sample.parquet")
        return ctx.call("flowweaver.std.io.import_dataset", path=path)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "data/sample.parquet")
        return {"out": io.import_dataset(path)}
