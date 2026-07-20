from typing import List
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_columns_exist

def drop_columns(dataset: Dataset, columns: List[str]) -> Dataset:
    """Drop specified columns from dataset."""
    validate_dataset(dataset)
    validate_columns_exist(dataset, columns)

    rows = dataset.to_list()
    new_cols = [c for c in dataset.columns() if c not in columns]
    new_rows = [{col: r.get(col) for col in new_cols} for r in rows]

    res = TabularDataset(
        new_rows,
        columns=new_cols,
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("drop_columns", columns=columns)
