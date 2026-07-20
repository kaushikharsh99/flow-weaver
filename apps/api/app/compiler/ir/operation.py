from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.compiler.ir.expression import IRExpression


@dataclass
class IROperation:
    """Represents a single pipeline step/operation in the IR."""
    id: str
    node_type: str
    target_variable: str
    expression: IRExpression
    inputs: Dict[str, str] = field(default_factory=dict)
    comment: Optional[str] = None
