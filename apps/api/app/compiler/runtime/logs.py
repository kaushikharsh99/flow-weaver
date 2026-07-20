from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ExecutionLogMessage:
    level: str  # "info" | "warning" | "error"
    message: str
    timestamp: Optional[str] = None


class LogCollector:
    """Collects and parses stdout/stderr lines from generated script execution."""

    def __init__(self):
        self.logs: List[ExecutionLogMessage] = []

    def add_line(self, line: str, is_stderr: bool = False):
        clean = line.strip()
        if not clean:
            return
        level = "error" if is_stderr else "info"
        if "warning" in clean.lower():
            level = "warning"
        elif "error" in clean.lower() or "exception" in clean.lower():
            level = "error"

        self.logs.append(ExecutionLogMessage(level=level, message=clean))
