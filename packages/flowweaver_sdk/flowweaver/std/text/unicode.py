import unicodedata
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_column_exists


def unicode_normalize(dataset: Dataset, column: str, form: str = "NFC") -> Dataset:
    """Applies Unicode normalization (NFC, NFD, NFKC, NFKD) to values in target column."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)

    valid_forms = ("NFC", "NFD", "NFKC", "NFKD")
    if form not in valid_forms:
        raise ValueError(f"Invalid Unicode normalization form '{form}'. Must be one of {valid_forms}")

    rows = dataset.to_list()
    new_rows = []
    for r in rows:
        row_copy = dict(r)
        val = row_copy.get(column)
        if val is not None:
            row_copy[column] = unicodedata.normalize(form, str(val))
        new_rows.append(row_copy)

    res = TabularDataset(
        new_rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("unicode_normalize", column=column, form=form)
