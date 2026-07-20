from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ColumnSchema:
    """Represents the schema definition of a dataset column."""
    name: str
    data_type: str = "string"
    nullable: bool = True


@dataclass
class DatasetSchema:
    """Represents the overall schema of a Dataset."""
    columns: List[ColumnSchema] = field(default_factory=list)

    @classmethod
    def infer_from_records(cls, records: List[Dict[str, Any]]) -> "DatasetSchema":
        if not records:
            return cls()
        
        cols = []
        sample_row = records[0]
        for name, val in sample_row.items():
            dtype = "string"
            if isinstance(val, bool):
                dtype = "boolean"
            elif isinstance(val, int):
                dtype = "integer"
            elif isinstance(val, float):
                dtype = "float"
            elif isinstance(val, (list, tuple)):
                dtype = "array"
            elif isinstance(val, dict):
                dtype = "struct"
            cols.append(ColumnSchema(name=name, data_type=dtype, nullable=val is None))
        return cls(columns=cols)

    def names(self) -> List[str]:
        return [c.name for c in self.columns]
