from typing import List, Any
from flowweaver.std.datasets import Dataset


def validate_dataset(dataset: Any) -> Dataset:
    """Ensures input is a valid FlowWeaver Dataset instance."""
    if not isinstance(dataset, Dataset):
        raise TypeError(f"Expected input to be an instance of flowweaver.std.Dataset, got {type(dataset).__name__}")
    return dataset


def validate_column_exists(dataset: Dataset, column: str) -> None:
    """Ensures the specified column exists in the dataset."""
    cols = dataset.columns()
    if column not in cols:
        raise ValueError(f"Column '{column}' not found in dataset columns: {cols}")


def validate_columns_exist(dataset: Dataset, columns: List[str]) -> None:
    """Ensures all specified columns exist in the dataset."""
    cols = set(dataset.columns())
    missing = [c for c in columns if c not in cols]
    if missing:
        raise ValueError(f"Columns {missing} not found in dataset columns: {list(cols)}")


def validate_not_empty(dataset: Dataset) -> None:
    """Ensures dataset contains at least 1 record."""
    rc = dataset.row_count()
    if rc is not None and rc == 0:
        raise ValueError("Operation cannot be performed on an empty dataset")
