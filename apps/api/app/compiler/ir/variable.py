from dataclasses import dataclass
from typing import Optional


@dataclass
class IRVariable:
    """Represents a named variable in the intermediate representation."""
    name: str
    type_hint: Optional[str] = None

    def __str__(self) -> str:
        return self.name
