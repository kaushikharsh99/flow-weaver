from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ValidationError(BaseModel):
    node_id: Optional[str] = Field(None, alias="nodeId")
    level: str  # error, warning, info
    message: str

    class Config:
        populate_by_name = True

class ValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationError] = []

class Task(BaseModel):
    id: str  # Task ID (typically same as node_id)
    node_id: str = Field(..., alias="nodeId")
    type_id: str = Field(..., alias="typeId")
    parameters: Dict[str, Any]
    dependencies: List[str]  # List of task IDs this task depends on
    inputs: Dict[str, Dict[str, str]]  # Maps: target_port -> {"source_node": "...", "source_port": "..."}
    is_cached: bool = Field(False, alias="isCached")

    class Config:
        populate_by_name = True

class ExecutionPlan(BaseModel):
    id: str
    pipeline_id: str = Field(..., alias="pipelineId")
    stages: List[List[Task]]  # Task layers that can run concurrently
    variables: Dict[str, Any]

    class Config:
        populate_by_name = True
