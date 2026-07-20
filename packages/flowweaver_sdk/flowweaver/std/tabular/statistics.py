from copy import deepcopy
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.datasets.metadata import DatasetMetadata
from flowweaver.std.utils.validation import validate_dataset

def statistics(dataset: Dataset) -> Dataset:
    """Compute column-level statistics. Returns dataset with statistics in metadata.extra."""
    validate_dataset(dataset)
    
    rows = dataset.to_list()
    columns = dataset.columns()
    
    stats = {}
    for col in columns:
        col_vals = [r.get(col) for r in rows]
        non_null_vals = [v for v in col_vals if v is not None]
        
        col_stats = {
            "count": len(col_vals),
            "nulls": len(col_vals) - len(non_null_vals),
            "unique": len(set(str(v) for v in col_vals))
        }
        
        numeric_vals = [v for v in non_null_vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric_vals:
            col_stats["min"] = min(numeric_vals)
            col_stats["max"] = max(numeric_vals)
            col_stats["mean"] = sum(numeric_vals) / len(numeric_vals) if numeric_vals else None
            
        stats[col] = col_stats

    new_metadata = deepcopy(dataset.metadata)
    new_metadata.extra["statistics"] = stats

    res = TabularDataset(
        rows,
        columns=columns,
        metadata=new_metadata,
        history=dataset.history
    )
    return res.with_history("statistics")

