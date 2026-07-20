from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from flowweaver.std import tabular, dedup


@node(name="Filter Rows", category="Filters", icon="Filter", description="Keep rows matching a condition")
class FilterRowsNode(Node):
    id = "filter_rows"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Filtered Rows")
    
    column = Param.column(label="Column", default="text")
    op = Param.select(label="Operator", default="==", options=[
        {"label": "==", "value": "=="}, {"label": "!=", "value": "!="}, {"label": ">", "value": ">"}, {"label": "<", "value": "<"}
    ])
    value = Param.text(label="Value", default="")

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "text")
        op = ctx.current_params.get("op", "==")
        val = ctx.current_params.get("value", "")
        return ctx.call("flowweaver.std.tabular.filter_rows", ctx.input_var, column=col, operator=op, value=val)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "text")
        op = ctx.parameters.get("op", "==")
        val = ctx.parameters.get("value", "")
        return {"out": tabular.filter_rows(dataset, column=col, operator=op, value=val)}


@node(name="Length Filter", category="Filters", icon="ArrowRight", description="Filter records by text column string length bounds")
class LengthFilterNode(Node):
    id = "length_filter"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Filtered Rows")
    
    column = Param.column(label="Target Column", default="text")
    min_len = Param.number(label="Min Length", default=10, min=0)
    max_len = Param.number(label="Max Length (optional)", default=1000, min=0)

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "text")
        min_l = ctx.current_params.get("min_len", 10)
        return ctx.call("flowweaver.std.tabular.filter_rows", ctx.input_var, column=col, operator="not_null", value="")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "text")
        return {"out": tabular.filter_rows(dataset, column=col, operator="not_null", value="")}


@node(name="Deduplicate Records", category="Dedup", icon="Copy", description="Remove duplicate records using Exact or SimHash algorithms")
class DedupNode(Node):
    id = "dedup_exact"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Deduplicated Rows")
    
    method = Param.select(label="Deduplication Algorithm", default="exact", options=[
        {"label": "Exact Matching", "value": "exact"},
        {"label": "SimHash (Near-duplicate text)", "value": "simhash"}
    ])
    column = Param.column(label="Target Column (for SimHash)", default="text")

    def compile(self, ctx: Any) -> Any:
        method = ctx.current_params.get("method", "exact")
        col = ctx.current_params.get("column", "text")
        if method == "simhash":
            return ctx.call("flowweaver.std.dedup.simhash_deduplicate", ctx.input_var, column=col, threshold=3)
        return ctx.call("flowweaver.std.dedup.dedup_exact", ctx.input_var)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        method = ctx.parameters.get("method", "exact")
        col = ctx.parameters.get("column", "text")
        if method == "simhash":
            return {"out": dedup.simhash_deduplicate(dataset, column=col, threshold=3)}
        return {"out": dedup.dedup_exact(dataset)}


@node(name="Sample", category="Filters", icon="Shuffle", description="Randomly sample N rows")
class SampleRowsNode(Node):
    id = "sample_rows"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    count = Param.number(label="Sample Size", default=100, min=1, max=100000)
    seed = Param.number(label="Random Seed", default=42)

    def compile(self, ctx: Any) -> Any:
        count = ctx.current_params.get("count", 100)
        seed = ctx.current_params.get("seed", 42)
        return ctx.dataset().sample_rows(n=count, seed=seed)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("rows")
        count = ctx.parameters.get("count", 100)
        seed = ctx.parameters.get("seed", 42)
        return {"output": tabular.sample_rows(dataset, n=count, seed=seed)}
