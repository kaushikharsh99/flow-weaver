import abc
from typing import Dict, Any, List

class ExecutionContext:
    def __init__(self, variables: Dict[str, Any], parameters: Dict[str, Any], inputs: Dict[str, Any]):
        self.variables = variables
        self.parameters = parameters
        self.inputs = inputs  # Maps: input_port_id -> value
        self.logs: List[str] = []

    def log(self, message: str):
        self.logs.append(message)

class BaseNode(abc.ABC):
    @abc.abstractmethod
    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """
        Execute the node logic.
        Returns a dictionary mapping: output_port_id -> value.
        """
        pass
