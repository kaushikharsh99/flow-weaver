from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from .context import ExecutionContext

class Port(BaseModel):
    id: str
    label: str
    type: str  # tabular, text, image, audio, any
    required: bool = False

    class Config:
        populate_by_name = True

class Parameter(BaseModel):
    key: str
    label: str
    type: str  # text, number, select, boolean, slider, textarea
    default: Optional[Any] = None
    placeholder: Optional[str] = ""
    options: Optional[List[Dict[str, str]]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None

    class Config:
        populate_by_name = True

class Node:
    """Base Node class that plugin builders inherit from."""
    id: str
    label: str
    category: str
    description: str
    icon: str
    color: str
    inputs: List[Port] = []
    outputs: List[Port] = []
    params_schema: List[Parameter] = []

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        """Execute implementation. Accepts inputs and returns dictionary mapping output port -> value."""
        raise NotImplementedError("Execute must be implemented by subclasses.")
