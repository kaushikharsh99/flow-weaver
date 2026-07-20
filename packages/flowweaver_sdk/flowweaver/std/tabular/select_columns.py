from typing import List
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_columns_exist


def select_columns(dataset: Dataset, columns: List[str]) -> Dataset:
    """Filters dataset fields to only include the specified target columns."""
    validate_dataset(dataset)
    validate_columns_exist(dataset, columns)

    rows = dataset.to_list()
    new_rows = [{col: r.get(col) for col in columns} for r in rows]

    res = TabularDataset(
        new_rows,
        columns=columns,
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("select_columns", columns=columns)
