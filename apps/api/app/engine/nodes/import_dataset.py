from typing import Dict, Any
from flowweaver.sdk import Node, Output, Param, node, ExecutionContext
from flowweaver.std import io


@node(name="Import Dataset", category="Loaders", icon="Sparkles", description="Intelligent Universal Import Engine with auto format/schema/type detection")
class ImportDatasetNode(Node):
    id = "import_dataset"
    out = Output.tabular(label="Dataset")
    
    path = Param.file(label="Dataset file or folder path", default="data/sample.csv")
    format = Param.select(label="Format", default="auto", options=[
        {"label": "Auto-detect", "value": "auto"},
        {"label": "CSV / TSV", "value": "csv"},
        {"label": "JSON", "value": "json"},
        {"label": "JSON Lines", "value": "jsonl"},
        {"label": "Parquet", "value": "parquet"}
    ])
    delimiter = Param.text(label="Delimiter (for CSV)", default=",")
    root_key = Param.text(label="Root key (for JSON)", default="")

    def compile(self, ctx: Any) -> Any:
        path = ctx.current_params.get("path", "data/sample.csv")
        fmt = ctx.current_params.get("format", "auto")
        ext = fmt.lower() if fmt and fmt != "auto" else (path.rsplit(".", 1)[-1].lower() if "." in path else "")
        delim = ctx.current_params.get("delimiter", ",")
        root_key = ctx.current_params.get("root_key", "")

        if ext in ("csv", "tsv"):
            actual_delim = "\t" if ext == "tsv" else delim
            return ctx.call("flowweaver.std.io.import_csv_dataset", path=path, delimiter=actual_delim)
        elif ext == "json":
            return ctx.call("flowweaver.std.io.import_json_dataset", path=path, root_key=root_key)
        elif ext in ("jsonl", "ndjson"):
            return ctx.call("flowweaver.std.io.import_jsonl_dataset", path=path)
        elif ext in ("parquet", "pq"):
            return ctx.call("flowweaver.std.io.import_parquet_dataset", path=path)
        else:
            return ctx.call("flowweaver.std.io.import_dataset", path=path, format=fmt, delimiter=delim, root_key=root_key)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        path = ctx.parameters.get("path", "data/sample.csv")
        fmt = ctx.parameters.get("format", "auto")
        fmt_arg = None if fmt == "auto" else fmt
        delim = ctx.parameters.get("delimiter", ",")
        root = ctx.parameters.get("root_key", "")
        dataset = io.import_dataset(path, format=fmt_arg, delimiter=delim, root_key=root)
        return {"out": dataset}

    def preview(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        exec_res = self.execute(inputs, ctx)
        dataset = exec_res.get("out")
        if dataset:
            return {"out": dataset, "preview": dataset.preview()}
        return {}
