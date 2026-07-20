import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db import get_db
from app import models, schemas

router = APIRouter()

@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    # Serialize SQLAlchemy models through Pydantic schema
    serialized = [schemas.ProjectResponse.model_validate(p).model_dump(by_alias=True) for p in projects]
    return {
        "data": serialized,
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
