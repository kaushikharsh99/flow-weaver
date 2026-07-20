from typing import List


class CodeBuilder:
    """Indentation-aware code builder for Python script generation."""

    def __init__(self, indent_str: str = "    "):
        self.indent_str = indent_str
        self.indent_level = 0
        self.lines: List[str] = []

    def line(self, content: str = ""):
        if content:
            self.lines.append((self.indent_str * self.indent_level) + content)
        else:
            self.lines.append("")

    def blank(self):
        self.lines.append("")

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level = max(0, self.indent_level - 1)

    def to_code(self) -> str:
        return "\n".join(self.lines) + "\n"
