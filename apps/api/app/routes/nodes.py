from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.engine.registry import registry

router = APIRouter()

@router.get("/nodes", response_model=Dict[str, List[Dict[str, Any]]])
def list_node_types():
    nodes = registry.list_all()
    nodes_data = []
    for node in nodes:
        data = node.dict(by_alias=True)
        data["type"] = data.pop("id")
        nodes_data.append(data)
    return {"data": nodes_data}

@router.get("/nodes/{node_type}", response_model=Dict[str, Dict[str, Any]])
def get_node_type(node_type: str):
    node = registry.get(node_type)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node type '{node_type}' not found.")
    data = node.dict(by_alias=True)
    data["type"] = data.pop("id")
    return {"data": data}

@router.post("/nodes/{node_type}/validate")
def validate_node(node_type: str, req: Dict[str, Any]):
    config = req.get("config", {})
    valid, errors = registry.validate_config(node_type, config)
    return {"data": {"valid": valid, "errors": [{"field": "", "issue": err} for err in errors]}}
