from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_column_exists


def sort_rows(dataset: Dataset, by: str, ascending: bool = True) -> Dataset:
    """Sorts dataset records by specified column in ascending or descending order."""
    validate_dataset(dataset)
    validate_column_exists(dataset, by)

    rows = dataset.to_list()
    # Safe sort key handling None
    sorted_rows = sorted(
        rows,
        key=lambda r: (r.get(by) is None, r.get(by)),
        reverse=not ascending
    )

    res = TabularDataset(
        sorted_rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("sort_rows", by=by, ascending=ascending)
