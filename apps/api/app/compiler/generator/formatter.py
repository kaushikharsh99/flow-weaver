import ast


class Formatter:
    """Formats Python source code using AST unparse or Ruff/Black if available."""

    @classmethod
    def format_code(cls, code: str) -> str:
        # Try AST unparse formatting first
        try:
            parsed = ast.parse(code)
            formatted = ast.unparse(parsed)
            return formatted + "\n"
        except Exception:
            return code
