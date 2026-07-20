import ast


class Formatter:
    """Formats Python source code while preserving comments and structure."""

    @classmethod
    def format_code(cls, code: str) -> str:
        # Validate that the code is syntactically correct Python
        try:
            ast.parse(code)
        except SyntaxError:
            pass  # Return raw code even if it has syntax issues

        # Clean up excessive blank lines (max 2 consecutive)
        lines = code.split("\n")
        cleaned = []
        blank_count = 0
        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)

        return "\n".join(cleaned)
