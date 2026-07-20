from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset

def concatenate(dataset: Dataset, other: Dataset) -> Dataset:
    """Vertically concatenate two datasets."""
    validate_dataset(dataset)
    validate_dataset(other)
    
    rows = dataset.to_list() + other.to_list()
    
    cols_seen = set()
    merged_cols = []
    for c in dataset.columns() + other.columns():
        if c not in cols_seen:
            merged_cols.append(c)
            cols_seen.add(c)
            
    res = TabularDataset(
        rows,
        columns=merged_cols,
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("concatenate")
