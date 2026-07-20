from typing import Any
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_column_exists


def filter_rows(
    dataset: Dataset,
    column: str,
    operator: str,
    value: Any
) -> Dataset:
    """Filters dataset records matching expression condition (eq, neq, gt, gte, lt, lte, contains, not_null, is_null)."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)

    rows = dataset.to_list()
    filtered = []

    for r in rows:
        val = r.get(column)
        keep = False

        if operator in ("==", "eq"):
            keep = (val == value)
        elif operator in ("!=", "neq"):
            keep = (val != value)
        elif operator in (">", "gt"):
            keep = (val is not None and val > value)
        elif operator in (">=", "gte"):
            keep = (val is not None and val >= value)
        elif operator in ("<", "lt"):
            keep = (val is not None and val < value)
        elif operator in ("<=", "lte"):
            keep = (val is not None and val <= value)
        elif operator in ("contains", "in"):
            keep = (val is not None and str(value) in str(val))
        elif operator in ("not_null", "is_not_null"):
            keep = (val is not None and str(val).strip() != "")
        elif operator in ("is_null", "null"):
            keep = (val is None or str(val).strip() == "")
        else:
            raise ValueError(f"Unsupported filter operator '{operator}'")

        if keep:
            filtered.append(r)

    res = TabularDataset(
        filtered,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("filter_rows", column=column, operator=operator, value=value)
