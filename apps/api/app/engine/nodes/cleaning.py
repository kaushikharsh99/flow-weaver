from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from app.engine.nodes.core_logic import (
    lowercase_text_column,
    strip_html_tags,
    remove_empty_records,
    unicode_normalize_text,
    regex_replace_text
)

@node(name="Lowercase Text", category="Transform", icon="Type", description="Convert a column's text values to lowercase")
class LowercaseNode(Node):
    id = "lowercase"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Modified Rows")
    column = Param.column(label="Target Column", default="text")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        return {"out": lowercase_text_column(dataset, col)}


@node(name="Strip HTML", category="Transform", icon="Code2", description="Remove HTML tags from text column content")
class StripHTMLNode(Node):
    id = "strip_html"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Cleaned Rows")
    column = Param.column(label="Target Column", default="text")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        return {"out": strip_html_tags(dataset, col)}


@node(name="Remove Empty Rows", category="Filters", icon="Trash", description="Drop rows where specified columns are empty or null")
class RemoveEmptyNode(Node):
    id = "remove_empty"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Cleaned Rows")
    columns = Param.text(label="Target Columns (comma-separated)", default="text", description="e.g. text, label")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        cols_str = ctx.parameters.get("columns", "")
        cols = [c.strip() for c in cols_str.split(",") if c.strip()]
        return {"out": remove_empty_records(dataset, cols)}


@node(name="Unicode Normalize", category="Transform", icon="SlidersHorizontal", description="Apply Unicode normalization standards (NFC, NFD, NFKC, NFKD)")
class UnicodeNormalizeNode(Node):
    id = "unicode_normalize"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Normalized Rows")
    column = Param.column(label="Target Column", default="text")
    form = Param.select(label="Normalization Form", default="NFC", options=[
        {"label": "NFC (Recommended)", "value": "NFC"},
        {"label": "NFD", "value": "NFD"},
        {"label": "NFKC", "value": "NFKC"},
        {"label": "NFKD", "value": "NFKD"}
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        form = ctx.parameters.get("form", "NFC")
        return {"out": unicode_normalize_text(dataset, col, form)}


@node(name="Regex Replace", category="Transform", icon="Wand2", description="Perform regular expression replacement on a text column")
class RegexReplaceNode(Node):
    id = "regex_replace"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Replaced Rows")
    column = Param.column(label="Target Column", default="text")
    pattern = Param.regex(label="Regex Pattern", default="\\s+", placeholder="e.g. \\s+")
    replacement = Param.text(label="Replacement", default=" ", placeholder="Replacement string")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        pattern = ctx.parameters.get("pattern", "")
        repl = ctx.parameters.get("replacement", "")
        return {"out": regex_replace_text(dataset, col, pattern, repl)}
