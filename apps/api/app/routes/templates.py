import uuid
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
