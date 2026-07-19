from fastapi import APIRouter, HTTPException
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
