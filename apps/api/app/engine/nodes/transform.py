import json
from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from flowweaver.std import tabular, text


@node(name="Rename Columns", category="Transform", icon="Columns3", description="Rename specific dataset columns")
class RenameColumnsNode(Node):
    id = "rename_columns"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Renamed Rows")
    
    mapping = Param.json(label="Rename Mapping (JSON)", default='{"old_name": "new_name"}', description="A JSON dictionary mapping old_name to new_name keys")

    def compile(self, ctx: Any) -> Any:
        mapping_str = ctx.current_params.get("mapping", '{"old_name": "new_name"}')
        try:
            mapping = json.loads(mapping_str) if isinstance(mapping_str, str) else mapping_str
        except Exception:
            mapping = {"old_name": "new_name"}
        return ctx.call("flowweaver.std.tabular.rename_columns", ctx.input_var, rename_map=mapping)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        mapping_str = ctx.parameters.get("mapping", '{"old_name": "new_name"}')
        try:
            mapping = json.loads(mapping_str) if isinstance(mapping_str, str) else mapping_str
        except Exception:
            mapping = {}
        return {"out": tabular.rename_columns(dataset, rename_map=mapping)}


@node(name="Select Columns", category="Transform", icon="Columns", description="Select target columns")
class SelectColumnsNode(Node):
    id = "select_columns"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Selected Rows")
    
    columns = Param.text(label="Columns (comma-separated)", default="text", description="e.g. id, text")

    def compile(self, ctx: Any) -> Any:
        cols_str = ctx.current_params.get("columns", "text")
        cols = [c.strip() for c in cols_str.split(",") if c.strip()]
        return ctx.call("flowweaver.std.tabular.select_columns", ctx.input_var, columns=cols)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        cols_str = ctx.parameters.get("columns", "text")
        cols = [c.strip() for c in cols_str.split(",") if c.strip()]
        return {"out": tabular.select_columns(dataset, columns=cols)}
