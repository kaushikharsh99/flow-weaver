import os

# Base directory for the backend API
api_base = "apps/api"

# Define the folder structure
folders = [
    api_base,
    f"{api_base}/app",
    f"{api_base}/app/routes",
    f"{api_base}/app/engine",
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Write package.json for workspace configuration
package_json = """{
  "name": "flow-weaver-api",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "uvicorn main:app --reload --port 8000"
  }
}
"""

with open(f"{api_base}/package.json", "w") as f:
    f.write(package_json)

# Write requirements.txt
requirements_txt = """fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.31
pydantic==2.7.4
pydantic-settings==2.3.4
websockets==12.0
python-multipart==0.0.9
"""

with open(f"{api_base}/requirements.txt", "w") as f:
    f.write(requirements_txt)

# Write main.py
main_py = """import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import projects, pipelines, nodes, executions, templates
from app.db import engine, Base

# Create database tables (SQLite in dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FlowWeaver API",
    description="Backend API for FlowWeaver Visual Pipeline Builder",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify front-end domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(pipelines.router, prefix="/api", tags=["Pipelines"])
app.include_router(nodes.router, prefix="/api", tags=["Nodes"])
app.include_router(executions.router, prefix="/api", tags=["Executions"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"""

with open(f"{api_base}/main.py", "w") as f:
    f.write(main_py)

# Write app/__init__.py
with open(f"{api_base}/app/__init__.py", "w") as f:
    pass

# Write app/config.py
config_py = """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./flow_weaver.db"
    SECRET_KEY: str = "super_secret_flow_weaver_key_change_me_in_production"
    
    class Config:
        env_file = ".env"

settings = Settings()
"""

with open(f"{api_base}/app/config.py", "w") as f:
    f.write(config_py)

# Write app/db.py
db_py = """from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# For SQLite, allow multi-threaded access (dev default)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

with open(f"{api_base}/app/db.py", "w") as f:
    f.write(db_py)

# Write app/models.py
models_py = """import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    pipelines = relationship("Pipeline", back_populates="project", cascade="all, delete-orphan")

class Pipeline(Base):
    __tablename__ = "pipelines"
    
    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    nodes = Column(JSON, default=list)  # Serialized Node list
    edges = Column(JSON, default=list)  # Serialized Edge list
    variables = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    viewport = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    project = relationship("Project", back_populates="pipelines")
    executions = relationship("Execution", back_populates="pipeline", cascade="all, delete-orphan")

class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(String, primary_key=True, index=True)
    pipeline_id = Column(String, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    pipeline = relationship("Pipeline", back_populates="executions")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    pipeline_data = Column(JSON, default=dict)  # Stores {nodes, edges}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
"""

with open(f"{api_base}/app/models.py", "w") as f:
    f.write(models_py)

# Write app/schemas.py
schemas_py = """from pydantic import BaseModel, Field
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
"""

with open(f"{api_base}/app/schemas.py", "w") as f:
    f.write(schemas_py)

# Write routes/__init__.py
routes_init = """# App Routers
"""
with open(f"{api_base}/app/routes/__init__.py", "w") as f:
    f.write(routes_init)

# Write routes/projects.py
projects_py = """import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app import models, schemas

router = APIRouter()

@router.get("/projects", response_model=Dict[str, Any])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    # Align with API contract wrapping: { "data": [...], "meta": { "total": n } }
    return {
        "data": projects,
        "meta": {"total": len(projects)}
    }

@router.post("/projects", response_model=Dict[str, schemas.ProjectResponse], status_code=status.HTTP_201_CREATED)
def create_project(project_in: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    project = models.Project(
        id=project_id,
        name=project_in.name,
        description=project_in.description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"data": project}

@router.get("/projects/{project_id}", response_model=Dict[str, schemas.ProjectResponse])
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": project}

@router.put("/projects/{project_id}", response_model=Dict[str, schemas.ProjectResponse])
def update_project(project_id: str, project_in: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
        
    db.commit()
    db.refresh(project)
    return {"data": project}

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None

# Add missing import for Dict, Any in router
from typing import Dict, Any
"""

with open(f"{api_base}/app/routes/projects.py", "w") as f:
    f.write(projects_py)

# Write routes/pipelines.py
pipelines_py = """import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db import get_db
from app import models, schemas

router = APIRouter()

@router.get("/projects/{project_id}/pipelines", response_model=Dict[str, List[schemas.PipelineSummaryResponse]])
def list_pipelines(project_id: str, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    pipelines = db.query(models.Pipeline).filter(models.Pipeline.project_id == project_id).all()
    return {"data": pipelines}

@router.post("/projects/{project_id}/pipelines", response_model=Dict[str, schemas.PipelineResponse], status_code=status.HTTP_201_CREATED)
def create_pipeline(project_id: str, pipeline_in: schemas.PipelineCreate, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    pipeline_id = f"pipe_{uuid.uuid4().hex[:8]}"
    pipeline = models.Pipeline(
        id=pipeline_id,
        project_id=project_id,
        name=pipeline_in.name,
        description=pipeline_in.description,
        nodes=[node.dict() for node in pipeline_in.nodes],
        edges=[edge.dict() for edge in pipeline_in.edges]
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return {"data": pipeline}

@router.get("/pipelines/{pipeline_id}", response_model=Dict[str, schemas.PipelineResponse])
def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"data": pipeline}

@router.put("/pipelines/{pipeline_id}", response_model=Dict[str, schemas.PipelineResponse])
def update_pipeline(pipeline_id: str, pipeline_in: schemas.PipelineUpdate, db: Session = Depends(get_db)):
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    update_data = pipeline_in.dict(exclude_unset=True)
    if "nodes" in update_data and update_data["nodes"] is not None:
        pipeline.nodes = [node.dict() for node in pipeline_in.nodes]
    if "edges" in update_data and update_data["edges"] is not None:
        pipeline.edges = [edge.dict() for edge in pipeline_in.edges]
        
    for field in ["name", "description", "variables", "settings", "viewport"]:
        if field in update_data and update_data[field] is not None:
            if field == "viewport":
                setattr(pipeline, field, update_data[field].dict() if hasattr(update_data[field], 'dict') else update_data[field])
            else:
                setattr(pipeline, field, update_data[field])
                
    db.commit()
    db.refresh(pipeline)
    return {"data": pipeline}

@router.delete("/pipelines/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    db.delete(pipeline)
    db.commit()
    return None

@router.post("/pipelines/{pipeline_id}/duplicate", response_model=Dict[str, schemas.PipelineResponse], status_code=status.HTTP_201_CREATED)
def duplicate_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    dup_id = f"pipe_{uuid.uuid4().hex[:8]}"
    dup_pipeline = models.Pipeline(
        id=dup_id,
        project_id=pipeline.project_id,
        name=f"{pipeline.name} (Copy)",
        description=pipeline.description,
        nodes=pipeline.nodes,
        edges=pipeline.edges,
        variables=pipeline.variables,
        settings=pipeline.settings,
        viewport=pipeline.viewport
    )
    db.add(dup_pipeline)
    db.commit()
    db.refresh(dup_pipeline)
    return {"data": dup_pipeline}
"""

with open(f"{api_base}/app/routes/pipelines.py", "w") as f:
    f.write(pipelines_py)

# Write routes/nodes.py
nodes_py = """from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

# Stub out node registries. Since backend engine will have its own python-based
# node registry, we return metadata mirroring the frontend or generic definitions.
@router.get("/nodes", response_model=Dict[str, List[Dict[str, Any]]])
def list_node_types():
    # Return placeholder node types mirroring the contract
    nodes = [
        {"type": "load_csv", "category": "Loaders", "label": "CSV Loader", "description": "Loads data from a CSV file."},
        {"type": "load_json", "category": "Loaders", "label": "JSON Loader", "description": "Parse a JSON array of records."},
        {"type": "filter_rows", "category": "Filters", "label": "Filter Rows", "description": "Keep rows matching a condition."}
    ]
    return {"data": nodes}

@router.get("/nodes/{node_type}", response_model=Dict[str, Dict[str, Any]])
def get_node_type(node_type: str):
    # Mirror complete details
    if node_type == "load_csv":
        data = {
            "type": "load_csv", "category": "Loaders", "label": "CSV Loader", "description": "Loads data from a CSV file.",
            "inputs": [],
            "outputs": [{"id": "out", "type": "dataset"}],
            "schema": {
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "delimiter": {"type": "string", "default": ","}
                },
                "required": ["filePath"]
            }
        }
        return {"data": data}
    raise HTTPException(status_code=404, detail="Node type not found")

@router.post("/nodes/{node_type}/validate")
def validate_node(node_type: str, req: Dict[str, Any]):
    # Allow all configurations for stub
    return {"data": {"valid": True, "errors": []}}
"""

with open(f"{api_base}/app/routes/nodes.py", "w") as f:
    f.write(nodes_py)

# Write routes/executions.py
executions_py = """import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db import get_db
from app import models, schemas
import asyncio
import json

router = APIRouter()

# Active WS connections for live updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, execution_id: str, websocket: WebSocket):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = []
        self.active_connections[execution_id].append(websocket)
        
    def disconnect(self, execution_id: str, websocket: WebSocket):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].remove(websocket)
            
    async def send_event(self, execution_id: str, event: Dict[str, Any]):
        if execution_id in self.active_connections:
            for connection in self.active_connections[execution_id]:
                await connection.send_text(json.dumps(event))

manager = ConnectionManager()

@router.post("/pipelines/{pipeline_id}/execute", response_model=Dict[str, Dict[str, Any]], status_code=status.HTTP_202_ACCEPTED)
def start_execution(pipeline_id: str, db: Session = Depends(get_db)):
    # Verify pipeline exists
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"
    execution = models.Execution(
        id=exec_id,
        pipeline_id=pipeline_id,
        status="pending",
        progress=0
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Simple background simulation of execution
    asyncio.create_task(simulate_pipeline_execution(exec_id, db))
    
    return {
        "data": {
            "executionId": execution.id,
            "status": execution.status,
            "startedAt": execution.started_at.isoformat() + "Z"
        }
    }

@router.get("/executions/{execution_id}", response_model=Dict[str, schemas.ExecutionResponse])
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    execution = db.query(models.Execution).filter(models.Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"data": execution}

@router.get("/executions/{execution_id}/logs", response_model=Dict[str, List[schemas.ExecutionLogEntry]])
def get_execution_logs(execution_id: str, db: Session = Depends(get_db)):
    # Return placeholder log entries
    logs = [
        {"timestamp": datetime.datetime.utcnow(), "level": "info", "message": "Starting engine execution..."},
        {"timestamp": datetime.datetime.utcnow(), "level": "info", "message": "Graph topological sort completed."},
    ]
    return {"data": logs}

@router.delete("/executions/{execution_id}", response_model=Dict[str, Dict[str, Any]])
def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    execution = db.query(models.Execution).filter(models.Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    execution.status = "cancelled"
    execution.completed_at = datetime.datetime.utcnow()
    db.commit()
    return {"data": {"id": execution.id, "status": execution.status}}

@router.websocket("/executions/{execution_id}/stream")
async def websocket_stream(websocket: WebSocket, execution_id: str):
    await manager.connect(execution_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(execution_id, websocket)

# Simulated background execution run
async def simulate_pipeline_execution(exec_id: str, db_session: Session):
    # Sleep to simulate starting delay
    await asyncio.sleep(1)
    
    # We create a local DB session to avoid threading conflicts with background task
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        execution = db.query(models.Execution).filter(models.Execution.id == exec_id).first()
        if not execution or execution.status == "cancelled":
            return
            
        execution.status = "running"
        db.commit()
        await manager.send_event(exec_id, {"type": "EXECUTION_STARTED", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"})
        
        # Simulate intermediate step progress
        steps = [("node_1", 25), ("node_2", 60), ("node_3", 90)]
        for node_id, progress in steps:
            await asyncio.sleep(1.5)
            execution = db.query(models.Execution).filter(models.Execution.id == exec_id).first()
            if execution.status == "cancelled":
                return
            execution.progress = progress
            db.commit()
            
            await manager.send_event(exec_id, {
                "type": "NODE_UPDATE",
                "nodeId": node_id,
                "status": "running",
                "progress": progress
            })
            await manager.send_event(exec_id, {
                "type": "LOG",
                "level": "info",
                "nodeId": node_id,
                "message": f"Step progress updated to {progress}%."
            })
            
        # Complete execution
        await asyncio.sleep(1)
        execution = db.query(models.Execution).filter(models.Execution.id == exec_id).first()
        if execution.status == "cancelled":
            return
        execution.status = "completed"
        execution.progress = 100
        execution.completed_at = datetime.datetime.utcnow()
        db.commit()
        
        await manager.send_event(exec_id, {"type": "EXECUTION_COMPLETED", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"})
    except Exception as e:
        execution = db.query(models.Execution).filter(models.Execution.id == exec_id).first()
        if execution:
            execution.status = "failed"
            execution.completed_at = datetime.datetime.utcnow()
            db.commit()
        await manager.send_event(exec_id, {
            "type": "EXECUTION_FAILED",
            "error": str(e),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })
    finally:
        db.close()
"""

with open(f"{api_base}/app/routes/executions.py", "w") as f:
    f.write(executions_py)

# Write routes/templates.py
templates_py = """import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db import get_db
from app import models, schemas

router = APIRouter()

@router.get("/templates", response_model=Dict[str, List[schemas.TemplateResponse]])
def list_templates(db: Session = Depends(get_db)):
    templates = db.query(models.Template).all()
    return {"data": templates}

@router.post("/templates", response_model=Dict[str, schemas.TemplateResponse], status_code=status.HTTP_201_CREATED)
def create_template(template_in: schemas.TemplateCreate, db: Session = Depends(get_db)):
    # Find referenced pipeline
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == template_in.pipelineId).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    tpl_id = f"tpl_{uuid.uuid4().hex[:8]}"
    template = models.Template(
        id=tpl_id,
        name=template_in.name,
        description=template_in.description,
        pipeline_data={
            "nodes": pipeline.nodes,
            "edges": pipeline.edges
        }
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"data": template}
"""

with open(f"{api_base}/app/routes/templates.py", "w") as f:
    f.write(templates_py)

# Write app/engine/__init__.py
engine_init = """# Core execution engine package
"""
with open(f"{api_base}/app/engine/__init__.py", "w") as f:
    f.write(engine_init)

print("Scaffolding backend completed successfully!")
