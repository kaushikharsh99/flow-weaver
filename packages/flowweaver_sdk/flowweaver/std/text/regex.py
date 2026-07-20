import re
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_column_exists


def regex_replace(
    dataset: Dataset,
    column: str,
    pattern: str,
    replacement: str
) -> Dataset:
    """Performs regular expression search-and-replace on target column values."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)

    compiled_re = re.compile(pattern)
    rows = dataset.to_list()
    new_rows = []
    for r in rows:
        row_copy = dict(r)
        val = row_copy.get(column)
        if val is not None:
            row_copy[column] = compiled_re.sub(replacement, str(val))
        new_rows.append(row_copy)

    res = TabularDataset(
        new_rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("regex_replace", column=column, pattern=pattern, replacement=replacement)
