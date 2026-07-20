from typing import Dict, Any, List
from app.compiler.ir import PipelineIR, IROperation, IRCall, IRConstant, IRVariable


from app.compiler.generator.builder import CodeBuilder
from app.compiler.generator.formatter import Formatter
from app.compiler.templates import get_header, get_footer


# Human-readable descriptions for node type operations
NODE_STEP_DESCRIPTIONS = {
    "import_dataset": "Import Dataset",
    "load_csv": "Import CSV Dataset",
    "load_json": "Import JSON Dataset",
    "load_jsonl": "Import JSON Lines Dataset",
    "load_parquet": "Import Parquet Dataset",
    "load_file": "Import Dataset",

    "lowercase": "Normalize Text to Lowercase",
    "uppercase": "Normalize Text to Uppercase",
    "unicode_normalize": "Apply Unicode Normalization",
    "strip_whitespace": "Strip Leading/Trailing Whitespace",
    "regex_replace": "Apply Regex Text Replacement",
    "strip_html": "Strip HTML Tags from Text",

    "filter_rows": "Filter Rows by Condition",
    "length_filter": "Filter Rows by Text Length",
    "remove_empty": "Remove Empty or Null Records",
    "sample_rows": "Sample Random Subset of Rows",

    "dedup_exact": "Deduplicate Records",
    "simhash_deduplicate": "Near-Duplicate Removal via SimHash",

    "select_columns": "Select Target Columns",
    "rename_columns": "Rename Dataset Columns",
    "drop_columns": "Drop Unused Columns",
    "sort_rows": "Sort Rows by Column",
    "shuffle": "Shuffle Dataset Rows",
    "split_dataset": "Split into Train/Test Sets",
    "concatenate": "Concatenate Datasets",

    "write_csv": "Export to CSV",
    "write_jsonl": "Export to JSON Lines",
    "write_parquet": "Export to Parquet",
    "export_csv": "Export to CSV",
    "export_jsonl": "Export to JSON Lines",
    "export_parquet": "Export to Parquet",
}

SECTION_SEPARATOR = "# " + "-" * 56


class PythonGenerator:
    """Translates PipelineIR into a clean, handwritten-quality Python script."""

    def __init__(self):
        self.builder = CodeBuilder()

    def generate(self, ir: PipelineIR) -> str:
        builder = CodeBuilder()

        # 1. Header Docstring
        builder.line(get_header(ir.name))
        builder.blank()

        # 2. Imports Section
        if ir.imports:
            for imp in ir.imports:
                builder.line(imp.to_statement())
            builder.blank()

        # 3. Main function definition
        builder.line("def main():")
        builder.indent()

        if not ir.operations:
            builder.line("pass")
        else:
            for step_num, op in enumerate(ir.operations, start=1):
                # Section separator with step number and description
                step_desc = NODE_STEP_DESCRIPTIONS.get(op.node_type, op.node_type.replace("_", " ").title())
                builder.line(SECTION_SEPARATOR)
                builder.line(f"# Step {step_num}: {step_desc}")
                builder.line(SECTION_SEPARATOR)

                call_expr = self._format_expression(op.expression)
                builder.line(f"{op.target_variable} = {call_expr}")
                builder.blank()

        builder.dedent()
        builder.blank()

        # 4. Footer script entrypoint
        builder.line(get_footer())

        raw_code = builder.to_code()
        return Formatter.format_code(raw_code)

    def _format_expression(self, expr: Any) -> str:
        if isinstance(expr, IRCall):
            args_list = []

            # Positional args
            for arg in expr.args:
                args_list.append(self._format_value(arg))

            # Kwargs
            for k, v in expr.kwargs.items():
                args_list.append(f"{k}={self._format_value(v)}")

            joined_args = ", ".join(args_list)
            return f"{expr.function}({joined_args})"
        elif isinstance(expr, IRConstant):
            return repr(expr.value)
        elif isinstance(expr, str):
            return expr
        else:
            return repr(expr)

    def _format_value(self, val: Any) -> str:
        if isinstance(val, IRVariable):
            return val.name
        elif isinstance(val, IRCall):
            return self._format_expression(val)
        elif isinstance(val, IRConstant):
            return repr(val.value)
        elif isinstance(val, str) and (val == "dataset" or val.startswith("dataset_") or val.endswith("_dataset")):
            return val
        else:
            return repr(val)
