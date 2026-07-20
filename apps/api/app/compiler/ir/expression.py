from dataclasses import dataclass, field
from typing import Any, Dict, List, Union


class IRExpression:
    """Base class for IR expressions."""
    pass


@dataclass
class IRConstant(IRExpression):
    """Represents a constant Python literal value."""
    value: Any

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass
class IRCall(IRExpression):
    """Represents a Python function call expression."""
    function: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
