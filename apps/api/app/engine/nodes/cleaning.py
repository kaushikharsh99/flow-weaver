from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from flowweaver.std import text, tabular


@node(name="Lowercase Text", category="Transform", icon="Type", description="Convert a column's text values to lowercase")
class LowercaseNode(Node):
    id = "lowercase"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Modified Rows")
    column = Param.column(label="Target Column", default="text")

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "text")
        return ctx.call("flowweaver.std.text.lowercase", ctx.input_var, column=col)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "text")
        return {"out": text.lowercase(dataset, column=col)}


@node(name="Strip HTML", category="Transform", icon="Code2", description="Remove HTML tags from text column content")
class StripHTMLNode(Node):
    id = "strip_html"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Cleaned Rows")
    column = Param.column(label="Target Column", default="text")

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "text")
        return ctx.call("flowweaver.std.text.regex_replace", ctx.input_var, column=col, pattern=r"<[^>]*>", replacement="")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "text")
        return {"out": text.regex_replace(dataset, column=col, pattern=r"<[^>]*>", replacement="")}


@node(name="Remove Empty Rows", category="Filters", icon="Trash", description="Drop rows where specified columns are empty or null")
class RemoveEmptyNode(Node):
    id = "remove_empty"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Cleaned Rows")
    columns = Param.text(label="Target Columns (comma-separated)", default="text", description="e.g. text, label")

    def compile(self, ctx: Any) -> Any:
        cols_str = ctx.current_params.get("columns", "text")
        first_col = [c.strip() for c in cols_str.split(",") if c.strip()][0] if cols_str else "text"
        return ctx.call("flowweaver.std.tabular.filter_rows", ctx.input_var, column=first_col, operator="not_null", value="")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        cols_str = ctx.parameters.get("columns", "text")
        first_col = [c.strip() for c in cols_str.split(",") if c.strip()][0] if cols_str else "text"
        return {"out": tabular.filter_rows(dataset, column=first_col, operator="not_null", value="")}


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

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "text")
        form = ctx.current_params.get("form", "NFC")
        return ctx.call("flowweaver.std.text.unicode_normalize", ctx.input_var, column=col, form=form)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "text")
        form = ctx.parameters.get("form", "NFC")
        return {"out": text.unicode_normalize(dataset, column=col, form=form)}


@node(name="Regex Replace", category="Transform", icon="Wand2", description="Perform regular expression replacement on a text column")
class RegexReplaceNode(Node):
    id = "regex_replace"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Replaced Rows")
    column = Param.column(label="Target Column", default="text")
    pattern = Param.regex(label="Regex Pattern", default="\\s+", placeholder="e.g. \\s+")
    replacement = Param.text(label="Replacement", default=" ", placeholder="Replacement string")

    def compile(self, ctx: Any) -> Any:
        col = ctx.current_params.get("column", "text")
        pattern = ctx.current_params.get("pattern", r"\s+")
        repl = ctx.current_params.get("replacement", " ")
        return ctx.call("flowweaver.std.text.regex_replace", ctx.input_var, column=col, pattern=pattern, replacement=repl)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "text")
        pattern = ctx.parameters.get("pattern", r"\s+")
        repl = ctx.parameters.get("replacement", " ")
        return {"out": text.regex_replace(dataset, column=col, pattern=pattern, replacement=repl)}
