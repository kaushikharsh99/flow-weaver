from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.compiler.validator import ValidationResult


@dataclass
class CompilerResult:
    """Encapsulates the complete result of compiling a FlowWeaver pipeline."""
    success: bool
    script: str
    script_path: Optional[str] = None
    validation: Optional[ValidationResult] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "script": self.script,
            "script_path": self.script_path,
            "warnings": self.warnings,
            "errors": self.errors,
            "statistics": self.statistics,
            "execution_time_ms": self.execution_time_ms
        }
