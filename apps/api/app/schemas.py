from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    createdAt: datetime = Field(..., alias="created_at")
    updatedAt: datetime = Field(..., alias="updated_at")

    class Config:
        populate_by_name = True
        from_attributes = True

# --- Pipeline Schemas ---
class ViewportSchema(BaseModel):
    x: float
    y: float
    zoom: float

class PipelineNodeSchema(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]

class PipelineEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str
    targetHandle: str

class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    nodes: Optional[List[PipelineNodeSchema]] = []
    edges: Optional[List[PipelineEdgeSchema]] = []

class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[PipelineNodeSchema]] = None
    edges: Optional[List[PipelineEdgeSchema]] = None
    variables: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    viewport: Optional[ViewportSchema] = None

class PipelineSummaryResponse(BaseModel):
    id: str
    projectId: str = Field(..., alias="project_id")
    name: str
    description: Optional[str] = ""
    createdAt: datetime = Field(..., alias="created_at")
    updatedAt: datetime = Field(..., alias="updated_at")

    class Config:
        populate_by_name = True
        from_attributes = True

class PipelineResponse(PipelineSummaryResponse):
    nodes: List[Any]
    edges: List[Any]
    variables: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
    viewport: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        from_attributes = True

# --- Execution Schemas ---
class ExecutionResponse(BaseModel):
    id: str
    pipelineId: str = Field(..., alias="pipeline_id")
    status: str
    progress: int
    startedAt: datetime = Field(..., alias="started_at")
    completedAt: Optional[datetime] = Field(None, alias="completed_at")

    class Config:
        populate_by_name = True
        from_attributes = True

class ExecutionLogEntry(BaseModel):
    timestamp: datetime
    level: str
    nodeId: Optional[str] = None
    message: str

# --- Template Schemas ---
class TemplateCreate(BaseModel):
    pipelineId: str
    name: str
    description: Optional[str] = ""

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    pipelineData: Dict[str, Any] = Field(..., alias="pipeline_data")
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        populate_by_name = True
        from_attributes = True
