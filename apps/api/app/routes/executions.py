import uuid
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

import threading
from app.db import SessionLocal
from app.engine.runner import execute_pipeline

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
    
    # Run the real pipeline execution engine in a background thread
    def run_in_thread():
        thread_db = SessionLocal()
        try:
            execute_pipeline(exec_id, thread_db, manager)
        finally:
            thread_db.close()
            
    threading.Thread(target=run_in_thread, daemon=True).start()
    
    return {
        "data": {
            "id": execution.id,
            "pipelineId": execution.pipeline_id,
            "status": execution.status,
            "progress": execution.progress,
            "startedAt": execution.started_at.isoformat() + "Z",
            "completedAt": None
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
