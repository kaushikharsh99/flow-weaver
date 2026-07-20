from typing import Dict
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_columns_exist


def rename_columns(dataset: Dataset, rename_map: Dict[str, str]) -> Dataset:
    """Renames specific dataset columns mapping keys (old names) to values (new names)."""
    validate_dataset(dataset)
    validate_columns_exist(dataset, list(rename_map.keys()))

    rows = dataset.to_list()
    new_rows = []
    for r in rows:
        new_row = {}
        for col, val in r.items():
            new_col = rename_map.get(col, col)
            new_row[new_col] = val
        new_rows.append(new_row)

    new_cols = [rename_map.get(col, col) for col in dataset.columns()]
    res = TabularDataset(
        new_rows,
        columns=new_cols,
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("rename_columns", rename_map=rename_map)
