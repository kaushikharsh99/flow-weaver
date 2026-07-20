import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class DatasetMetadata:
    """Stores metadata information for a Dataset instance."""
    rows: Optional[int] = None
    columns: int = 0
    memory_bytes: Optional[int] = None
    source: Optional[str] = None
    encoding: str = "utf-8"
    created_at: float = field(default_factory=time.time)
    extra: Dict[str, Any] = field(default_factory=dict)
