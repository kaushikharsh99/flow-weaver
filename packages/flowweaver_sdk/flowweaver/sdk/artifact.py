from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class Artifact(BaseModel):
    id: str
    name: str
    type: str  # dataset, schema, file, metric
    path: str  # local storage filepath or key
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
