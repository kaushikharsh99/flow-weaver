from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class IRImport:
    """Represents an import statement in Python code."""
    module: str
    alias: Optional[str] = None
    names: Optional[List[str]] = None

    def to_statement(self) -> str:
        """Convert IRImport into Python code statement."""
        if self.names:
            names_str = ", ".join(self.names)
            return f"from {self.module} import {names_str}"
        elif self.alias:
            return f"import {self.module} as {self.alias}"
        else:
            return f"import {self.module}"
