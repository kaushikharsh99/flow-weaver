import time
from typing import Dict, Any, List, Optional, Callable
from .artifact import Artifact

class Logger:
    def __init__(self):
        self.logs: List[str] = []

    def info(self, msg: str):
        self.logs.append(f"[INFO] {msg}")

    def warn(self, msg: str):
        self.logs.append(f"[WARN] {msg}")

    def error(self, msg: str):
        self.logs.append(f"[ERROR] {msg}")

class Metrics:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.memory_bytes: int = 0
        self.cpu_percentage: float = 0.0

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def duration_ms(self) -> int:
        end = self.end_time or time.perf_counter()
        return int((end - self.start_time) * 1000)

class ExecutionContext:
    def __init__(self, variables: Dict[str, Any], parameters: Dict[str, Any]):
        self.variables = variables
        self.parameters = parameters
        self.logger = Logger()
        self.metrics = Metrics()
        self.artifacts: List[Artifact] = []
        
        # Callback hooks for status & runtime coordination
        self._progress_callback: Optional[Callable[[int, Optional[str]], None]] = None
        self._cancel_check: Optional[Callable[[], bool]] = None

    def log(self, message: str):
        self.logger.info(message)
        
    def log_warn(self, message: str):
        self.logger.warn(message)
        
    def log_error(self, message: str):
        self.logger.error(message)

    def add_artifact(self, artifact: Artifact):
        self.artifacts.append(artifact)

    def report_progress(self, percent: int, message: Optional[str] = None):
        """Report internal task execution progress percentage (0-100) and an optional status message."""
        percent_capped = max(0, min(100, int(percent)))
        if message:
            self.log(message)
        if self._progress_callback:
            self._progress_callback(percent_capped, message)

    def is_cancelled(self) -> bool:
        """Check if execution has been cancelled by user in the visual workspace."""
        if self._cancel_check:
            return self._cancel_check()
        return False
