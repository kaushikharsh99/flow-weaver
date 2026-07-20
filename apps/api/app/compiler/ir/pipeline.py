from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.compiler.ir.operation import IROperation
from app.compiler.ir.imports import IRImport
from app.compiler.ir.variable import IRVariable


@dataclass
class PipelineIR:
    """Complete Intermediate Representation of a FlowWeaver pipeline."""
    name: str
    operations: List[IROperation] = field(default_factory=list)
    imports: List[IRImport] = field(default_factory=list)
    variables: List[IRVariable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
