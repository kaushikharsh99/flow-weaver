from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_column_exists


def uppercase(dataset: Dataset, column: str) -> Dataset:
    """Converts string values in the specified column to uppercase."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)

    rows = dataset.to_list()
    new_rows = []
    for r in rows:
        row_copy = dict(r)
        val = row_copy.get(column)
        if val is not None:
            row_copy[column] = str(val).upper()
        new_rows.append(row_copy)

    res = TabularDataset(
        new_rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("uppercase", column=column)
