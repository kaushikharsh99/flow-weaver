import json
from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext, Port
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


@node(name="Drop Columns", category="Transform", icon="Trash2", description="Remove unwanted columns from dataset")
class DropColumnsNode(Node):
    id = "drop_columns"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Trimmed Rows")

    columns = Param.text(label="Columns to Drop (comma-separated)", default="", description="e.g. __index_level_0__, Unnamed: 0")

    def compile(self, ctx: Any) -> Any:
        cols_str = ctx.current_params.get("columns", "")
        cols = [c.strip() for c in cols_str.split(",") if c.strip()]
        return ctx.dataset().drop_columns(columns=cols)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        cols_str = ctx.parameters.get("columns", "")
        cols = [c.strip() for c in cols_str.split(",") if c.strip()]
        return {"out": tabular.drop_columns(dataset, columns=cols)}


@node(name="Sort Rows", category="Transform", icon="ArrowUpDown", description="Sort dataset rows by a column")
class SortRowsNode(Node):
    id = "sort_rows"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Sorted Rows")

    column = Param.column(label="Sort Column", default="id")
    ascending = Param.boolean(label="Ascending", default=True)

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "id")
        asc = ctx.current_params.get("ascending", True)
        return ctx.dataset().sort_rows(by=col, ascending=asc)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "id")
        asc = ctx.parameters.get("ascending", True)
        return {"out": tabular.sort_rows(dataset, by=col, ascending=asc)}


@node(name="Shuffle", category="Transform", icon="Shuffle", description="Randomly shuffle all rows")
class ShuffleNode(Node):
    id = "shuffle"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Shuffled Rows")

    seed = Param.number(label="Random Seed", default=42)

    def compile(self, ctx: Any) -> Any:
        seed = ctx.current_params.get("seed", 42)
        return ctx.dataset().shuffle(seed=seed)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        seed = ctx.parameters.get("seed", 42)
        return {"out": tabular.shuffle(dataset, seed=seed)}


@node(name="Split Dataset", category="Transform", icon="GitBranch", description="Split dataset into train/test sets by ratio")
class SplitDatasetNode(Node):
    id = "split_dataset"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Train Set")

    ratio = Param.slider(label="Train Ratio", default=0.8, min=0.0, max=1.0, step=0.05)
    seed = Param.number(label="Random Seed", default=42)

    def compile(self, ctx: Any) -> Any:
        ratio = ctx.current_params.get("ratio", 0.8)
        seed = ctx.current_params.get("seed", 42)
        return ctx.dataset().split_dataset(ratio=ratio, seed=seed)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        ratio = ctx.parameters.get("ratio", 0.8)
        seed = ctx.parameters.get("seed", 42)
        train, test = tabular.split_dataset(dataset, ratio=ratio, seed=seed)
        # Primary output is train set; test set available via metadata
        return {"out": train}


@node(name="Concatenate", category="Transform", icon="Layers", description="Vertically concatenate two datasets")
class ConcatenateNode(Node):
    id = "concatenate"
    inputs = [
        Port(id="first", label="first", type="tabular", required=True),
        Port(id="second", label="second", type="tabular", required=True),
    ]
    out = Output.tabular(label="Combined Rows")

    def compile(self, ctx: Any) -> Any:
        # For concatenate, we need both input variables
        return ctx.dataset().concatenate(other_var=ctx.input_var)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        first = inputs.get("first")
        second = inputs.get("second")
        return {"out": tabular.concatenate(first, second)}

