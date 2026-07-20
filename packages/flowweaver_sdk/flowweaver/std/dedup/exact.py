from typing import Optional, List
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_columns_exist


def dedup_exact(dataset: Dataset, columns: Optional[List[str]] = None) -> Dataset:
    """Removes duplicate rows based on exact match across target columns (or all columns if None)."""
    validate_dataset(dataset)
    if columns:
        validate_columns_exist(dataset, columns)

    rows = dataset.to_list()
    seen = set()
    deduped = []

    for r in rows:
        if columns:
            key = tuple(r.get(c) for c in columns)
        else:
            key = tuple(sorted((k, str(v)) for k, v in r.items()))

        if key not in seen:
            seen.add(key)
            deduped.append(r)

    res = TabularDataset(
        deduped,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("dedup_exact", columns=columns)
