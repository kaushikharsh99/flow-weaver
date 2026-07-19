import datetime
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
