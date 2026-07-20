from typing import Dict, Any, List
from app.compiler.ir import PipelineIR, IROperation, IRCall, IRConstant
from app.compiler.generator.builder import CodeBuilder
from app.compiler.generator.formatter import Formatter
from app.compiler.templates import get_header, get_footer


class PythonGenerator:
    """Translates PipelineIR into a clean, runnable Python script."""

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
            for op in ir.operations:
                if op.comment:
                    builder.line(f"# {op.comment}")

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
        if isinstance(val, IRCall):
            return self._format_expression(val)
        elif isinstance(val, IRConstant):
            return repr(val.value)
        elif isinstance(val, str) and (val.startswith("dataset") or val.isidentifier()):
            # Variable reference vs string literal
            if val in ("True", "False", "None"):
                return val
            return repr(val)
        else:
            return repr(val)
