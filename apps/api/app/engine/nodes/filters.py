from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext, TabularDataset
from app.engine.nodes.core_logic import filter_by_text_length, filter_by_detected_language, deduplicate_records

@node(name="Filter Rows", category="Filters", icon="Filter", description="Keep rows matching a condition")
class FilterRowsNode(Node):
    id = "filter_rows"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Filtered Rows")
    
    column = Param.column(label="Column", default="age")
    op = Param.select(label="Operator", default=">", options=[
        {"label": ">", "value": ">"}, {"label": "<", "value": "<"}, {"label": "=", "value": "="}, {"label": "!=", "value": "!="}
    ])
    value = Param.text(label="Value", default="25")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {"out": TabularDataset([], columns=[])}
            
        columns = dataset.columns()
        rows_dicts = dataset.to_list()
        
        col_name = ctx.parameters.get("column", "")
        operator = ctx.parameters.get("op", "=")
        filter_val = ctx.parameters.get("value", "")
        
        if col_name not in columns:
            return {"out": dataset}
            
        filtered_rows = []
        for row in rows_dicts:
            cell_val = str(row.get(col_name, "")).strip()
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
        return {"out": TabularDataset(filtered_rows, columns=columns)}


@node(name="Length Filter", category="Filters", icon="ArrowRight", description="Filter records by text column string length bounds")
class LengthFilterNode(Node):
    id = "length_filter"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Filtered Rows")
    
    column = Param.column(label="Target Column", default="text")
    min_len = Param.number(label="Min Length", default=10, min=0)
    max_len = Param.number(label="Max Length (optional)", default=1000, min=0)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        min_l = int(ctx.parameters.get("min_len", 10))
        max_l = ctx.parameters.get("max_len")
        max_l_val = int(max_l) if max_l is not None and str(max_l).strip() != "" else None
        return {"out": filter_by_text_length(dataset, col, min_l, max_l_val)}


@node(name="Language Filter", category="Filters", icon="Languages", description="Keep records matching a target language (e.g. English)")
class LanguageFilterNode(Node):
    id = "language_filter"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Filtered Rows")
    
    column = Param.column(label="Text Column", default="text")
    target_lang = Param.select(label="Target Language", default="en", options=[
        {"label": "English (en)", "value": "en"},
        {"label": "Other (non-en)", "value": "other"}
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        lang = ctx.parameters.get("target_lang", "en")
        return {"out": filter_by_detected_language(dataset, col, lang)}


@node(name="Deduplicate Records", category="Dedup", icon="Copy", description="Remove duplicate records using Exact, Hash, SimHash, or MinHash Jaccard algorithms")
class DedupNode(Node):
    id = "dedup_exact"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Deduplicated Rows")
    
    method = Param.select(label="Deduplication Algorithm", default="exact", options=[
        {"label": "Exact Matching", "value": "exact"},
        {"label": "Hash matching (xxHash/SHA256)", "value": "hash"},
        {"label": "SimHash (Near-duplicate text)", "value": "simhash"},
        {"label": "MinHash (Jaccard similarity)", "value": "minhash"}
    ])
    column = Param.column(label="Target Column (for Hash/SimHash/MinHash)", default="text")
    columns = Param.text(label="Key Columns (for Exact match, comma-separated)", default="", description="e.g. id, name (leave blank to check all)")
    threshold = Param.slider(label="MinHash Jaccard Threshold", default=0.85, min=0.0, max=1.0, step=0.01)
    max_hamming = Param.number(label="SimHash Max Hamming Distance (bits)", default=3, min=0, max=64)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        method = ctx.parameters.get("method", "exact")
        col = ctx.parameters.get("column", "")
        cols_str = ctx.parameters.get("columns", "")
        cols = [c.strip() for c in cols_str.split(",") if c.strip()] if cols_str else None
        threshold = float(ctx.parameters.get("threshold", 0.85))
        max_hamming = int(ctx.parameters.get("max_hamming", 3))
        
        return {"out": deduplicate_records(
            dataset=dataset, 
            columns=cols,
            column=col,
            method=method,
            threshold=threshold,
            max_hamming_dist=max_hamming
        )}
