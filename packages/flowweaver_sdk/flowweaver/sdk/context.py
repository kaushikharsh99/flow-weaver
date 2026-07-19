import time
from typing import Dict, Any, List, Optional
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

    def log(self, message: str):
        self.logger.info(message)
        
    def log_warn(self, message: str):
        self.logger.warn(message)
        
    def log_error(self, message: str):
        self.logger.error(message)

    def add_artifact(self, artifact: Artifact):
        self.artifacts.append(artifact)
