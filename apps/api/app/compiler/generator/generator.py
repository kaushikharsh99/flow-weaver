from typing import Dict, Any, List, Optional, Tuple
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
    "statistics": "Compute Dataset Statistics",

    "write_csv": "Export to CSV",
    "write_jsonl": "Export to JSON Lines",
    "write_parquet": "Export to Parquet",
    "export_csv": "Export to CSV",
    "export_jsonl": "Export to JSON Lines",
    "export_parquet": "Export to Parquet",
}

# Node types that are import/load operations
IMPORT_NODE_TYPES = {
    "import_dataset", "load_file", "load_csv", "load_json", "load_jsonl", "load_parquet"
}

# Node types that are export/write operations
EXPORT_NODE_TYPES = {
    "write_csv", "write_jsonl", "write_parquet",
    "export_csv", "export_jsonl", "export_parquet"
}

SECTION_SEPARATOR = "# " + "-" * 56


class PythonGenerator:
    """Translates PipelineIR into a clean, handwritten-quality Python script."""

    def __init__(self):
        self.builder = CodeBuilder()

    def generate(self, ir: PipelineIR) -> str:
        builder = CodeBuilder()
        total_steps = len(ir.operations)

        # Detect input/output paths for argparse
        input_path, output_path = self._detect_io_paths(ir)

        # 1. Header Docstring
        builder.line(get_header(ir.name))
        builder.blank()

        # 2. Standard library base imports
        builder.line("import argparse")
        builder.line("import logging")
        builder.line("import time")
        builder.blank()

        # 3. Resolve and Inline Operations using PipelineLinker
        from app.compiler.linker import PipelineLinker
        linker = PipelineLinker()
        
        required_ops = []
        for op in ir.operations:
            if isinstance(op.expression, IRCall):
                func_name = op.expression.function
                if func_name in linker.name_to_file:
                    required_ops.append(func_name)

        inlined_code, requirements = linker.link(required_ops)
        ir.metadata["requirements"] = requirements
        
        if inlined_code:
            builder.line(inlined_code)
            builder.blank()

        # 4. Logging setup
        builder.line(SECTION_SEPARATOR)
        builder.line("# Logging Configuration")
        builder.line(SECTION_SEPARATOR)
        builder.line('logging.basicConfig(')
        builder.line('    level=logging.INFO,')
        builder.line('    format="%(asctime)s [%(levelname)s] %(message)s",')
        builder.line('    datefmt="%H:%M:%S"')
        builder.line(')')
        builder.line('logger = logging.getLogger("flowweaver.pipeline")')
        builder.blank()
        builder.blank()

        # 5. Parse args function
        builder.line("def parse_args():")
        builder.indent()
        safe_name = ir.name.replace("_", " ").title()
        builder.line(f'parser = argparse.ArgumentParser(description="{safe_name} — FlowWeaver Pipeline")')
        if input_path:
            builder.line(f'parser.add_argument("--input", default="{input_path}", help="Input dataset path")')
        if output_path:
            builder.line(f'parser.add_argument("--output", default="{output_path}", help="Output file path")')
        builder.line('parser.add_argument("--dry-run", action="store_true", help="Validate pipeline without writing output")')
        builder.line('parser.add_argument("--verbose", action="store_true", help="Enable debug logging")')
        builder.line("return parser.parse_args()")
        builder.dedent()
        builder.blank()
        builder.blank()

        # 6. Main function definition
        builder.line("def main():")
        builder.indent()

        # Args + verbose setup
        builder.line("args = parse_args()")
        builder.line("if args.verbose:")
        builder.indent()
        builder.line("logging.getLogger().setLevel(logging.DEBUG)")
        builder.dedent()
        builder.blank()

        # Pipeline start banner
        builder.line(f'logger.info("Starting pipeline: {ir.name}")')
        builder.line("pipeline_start = time.time()")
        builder.blank()

        if not ir.operations:
            builder.line("pass")
        else:
            for step_num, op in enumerate(ir.operations, start=1):
                # Section separator with step number and description
                step_desc = NODE_STEP_DESCRIPTIONS.get(op.node_type, op.node_type.replace("_", " ").title())
                builder.line(SECTION_SEPARATOR)
                builder.line(f"# Step {step_num}/{total_steps}: {step_desc}")
                builder.line(SECTION_SEPARATOR)

                # Progress log
                builder.line(f'logger.info("Step {step_num}/{total_steps}: {step_desc}")')

                # Build the actual call expression, substituting argparse vars for paths
                call_expr = self._format_expression(op.expression, input_path, output_path)

                # For import nodes, use args.input if available
                if op.node_type in IMPORT_NODE_TYPES and input_path:
                    call_expr = self._substitute_path_arg(call_expr, input_path, "args.input")

                # For export nodes, treat as terminal operation (no variable assignment)
                if op.node_type in EXPORT_NODE_TYPES:
                    if output_path:
                        call_expr = self._substitute_path_arg(call_expr, output_path, "args.output")
                    builder.line(f"{call_expr}")
                else:
                    builder.line(f"{op.target_variable} = {call_expr}")
                builder.blank()

        # Pipeline completion
        builder.line("elapsed = time.time() - pipeline_start")
        builder.line(f'logger.info(f"Pipeline completed in {{elapsed:.2f}}s")')

        builder.dedent()
        builder.blank()
        builder.blank()

        # 7. Footer script entrypoint
        builder.line(get_footer())

        raw_code = builder.to_code()
        return Formatter.format_code(raw_code)

    def _detect_io_paths(self, ir: PipelineIR) -> Tuple[Optional[str], Optional[str]]:
        """Extract the first input path and last output path from pipeline operations."""
        input_path = None
        output_path = None

        for op in ir.operations:
            if isinstance(op.expression, IRCall):
                path_val = op.expression.kwargs.get("path")
                if path_val is not None:
                    path_str = path_val.value if isinstance(path_val, IRConstant) else str(path_val)
                    if op.node_type in IMPORT_NODE_TYPES and input_path is None:
                        input_path = path_str
                    elif op.node_type in EXPORT_NODE_TYPES:
                        output_path = path_str

        return input_path, output_path

    def _substitute_path_arg(self, call_expr: str, literal_path: str, arg_ref: str) -> str:
        """Replace a literal path string with an argparse reference."""
        return call_expr.replace(f"'{literal_path}'", arg_ref).replace(f'"{literal_path}"', arg_ref)

    def _format_expression(self, expr: Any, input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
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
