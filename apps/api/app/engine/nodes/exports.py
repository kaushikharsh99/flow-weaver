from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from flowweaver.std import io


@node(name="Write CSV", category="Export", icon="Save", description="Serialize records to a CSV file")
class WriteCSVNode(Node):
    id = "write_csv"
    in_data = Input.tabular(label="Rows")
    path = Param.file(label="Output path", default="out/results.csv", accept=".csv")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "out/results.csv")
        return ctx.call("flowweaver.std.io.export_csv", ctx.input_var, path=path)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
        path = ctx.parameters.get("path", "out/results.csv")
        return {"out": io.export_csv(dataset, path=path)}


@node(name="Write JSON Lines", category="Export", icon="Download", description="Serialize dataset records into JSON Lines format")
class WriteJSONLNode(Node):
    id = "write_jsonl"
    in_data = Input.tabular(label="Rows")
    path = Param.file(label="Output path", default="out/results.jsonl", accept=".jsonl")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "out/results.jsonl")
        return ctx.call("flowweaver.std.io.export_jsonl", ctx.input_var, path=path)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
        path = ctx.parameters.get("path", "out/results.jsonl")
        return {"out": io.export_jsonl(dataset, path=path)}


@node(name="Write Parquet", category="Export", icon="FolderArchive", description="Serialize dataset records into Parquet format")
class WriteParquetNode(Node):
    id = "write_parquet"
    in_data = Input.tabular(label="Rows")
    path = Param.file(label="Output path", default="out/results.parquet", accept=".parquet")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "out/results.parquet")
        return ctx.call("flowweaver.std.io.export_parquet", ctx.input_var, path=path)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
        path = ctx.parameters.get("path", "out/results.parquet")
        return {"out": io.export_parquet(dataset, path=path)}
