import sys
import time
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.compiler.runtime.logs import LogCollector, ExecutionLogMessage
from app.compiler.runtime.environment import get_execution_environment


@dataclass
class ExecutionResult:
    """Result of running a generated Python pipeline script."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    logs: List[ExecutionLogMessage] = field(default_factory=list)


class PythonExecutor:
    """Executes compiled Python scripts directly via Python interpreter subprocess."""

    @classmethod
    def execute_script(cls, script_path: str, timeout_sec: int = 300) -> ExecutionResult:
        collector = LogCollector()
        start_time = time.time()
        env = get_execution_environment()

        try:
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            stdout, stderr = process.communicate(timeout=timeout_sec)
            duration_ms = (time.time() - start_time) * 1000.0

            for line in stdout.splitlines():
                collector.add_line(line, is_stderr=False)

            for line in stderr.splitlines():
                collector.add_line(line, is_stderr=True)

            return ExecutionResult(
                success=(process.returncode == 0),
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                logs=collector.logs
            )
        except subprocess.TimeoutExpired:
            process.kill()
            duration_ms = (time.time() - start_time) * 1000.0
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Script execution timed out after {timeout_sec} seconds.",
                duration_ms=duration_ms,
                logs=[ExecutionLogMessage(level="error", message="Execution timeout")]
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                logs=[ExecutionLogMessage(level="error", message=str(e))]
            )
