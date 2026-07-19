import uuid
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
