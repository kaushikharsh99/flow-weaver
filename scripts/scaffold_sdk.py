import os

sdk_dir = "packages/flowweaver_sdk"
os.makedirs(f"{sdk_dir}/flowweaver/sdk", exist_ok=True)

# 1. Write setup.py
setup_py = """from setuptools import setup, find_packages

setup(
    name="flowweaver-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_packages=["pydantic>=2.0.0"],
    author="FlowWeaver Team",
    description="Core developer SDK for writing FlowWeaver nodes and plugins",
    python_requires=">=3.8",
)
"""
with open(f"{sdk_dir}/setup.py", "w") as f:
    f.write(setup_py)

# 2. Write flowweaver/sdk/__init__.py
sdk_init = """from .dataset import Dataset, TabularDataset
from .context import ExecutionContext, Logger, Metrics
from .node import Node, Port, Parameter
from .artifact import Artifact

__all__ = [
    "Dataset",
    "TabularDataset",
    "ExecutionContext",
    "Logger",
    "Metrics",
    "Node",
    "Port",
    "Parameter",
    "Artifact",
]
"""
with open(f"{sdk_dir}/flowweaver/sdk/__init__.py", "w") as f:
    f.write(sdk_init)

# 3. Write flowweaver/sdk/dataset.py
dataset_py = """import abc
from typing import List, Dict, Any, Optional

class Dataset(abc.ABC):
    @abc.abstractmethod
    def to_list(self) -> List[Dict[str, Any]]:
        \"\"\"Convert dataset to list of dicts (tabular).\"\"\"
        pass

    @abc.abstractmethod
    def columns(self) -> List[str]:
        \"\"\"Return list of dataset columns.\"\"\"
        pass
        
    @abc.abstractmethod
    def row_count(self) -> int:
        \"\"\"Return number of rows.\"\"\"
        pass

class TabularDataset(Dataset):
    \"\"\"Standard in-memory list-of-dicts tabular dataset.\"\"\"
    def __init__(self, data: List[Dict[str, Any]], columns: Optional[List[str]] = None):
        self._data = data
        if columns is not None:
            self._columns = columns
        else:
            self._columns = list(data[0].keys()) if data else []
        
    def to_list(self) -> List[Dict[str, Any]]:
        return self._data
        
    def columns(self) -> List[str]:
        return self._columns
        
    def row_count(self) -> int:
        return len(self._data)
"""
with open(f"{sdk_dir}/flowweaver/sdk/dataset.py", "w") as f:
    f.write(dataset_py)

# 4. Write flowweaver/sdk/context.py
context_py = """import time
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
"""
with open(f"{sdk_dir}/flowweaver/sdk/context.py", "w") as f:
    f.write(context_py)

# 5. Write flowweaver/sdk/artifact.py
artifact_py = """from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class Artifact(BaseModel):
    id: str
    name: str
    type: str  # dataset, schema, file, metric
    path: str  # local storage filepath or key
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
"""
with open(f"{sdk_dir}/flowweaver/sdk/artifact.py", "w") as f:
    f.write(artifact_py)

# 6. Write flowweaver/sdk/node.py
node_py = """from pydantic import BaseModel, Field
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
    \"\"\"Base Node class that plugin builders inherit from.\"\"\"
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
        \"\"\"Execute implementation. Accepts inputs and returns dictionary mapping output port -> value.\"\"\"
        raise NotImplementedError("Execute must be implemented by subclasses.")
"""
with open(f"{sdk_dir}/flowweaver/sdk/node.py", "w") as f:
    f.write(node_py)

print("Scaffolding FlowWeaver SDK completed successfully!")
