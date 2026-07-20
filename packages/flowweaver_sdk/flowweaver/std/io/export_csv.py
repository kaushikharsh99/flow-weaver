import os
import csv
from flowweaver.std.datasets import Dataset
from flowweaver.std.utils.validation import validate_dataset


def export_csv(dataset: Dataset, path: str, delimiter: str = ",") -> Dataset:
    """Exports dataset records into a CSV file."""
    validate_dataset(dataset)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    records = dataset.to_list()
    cols = dataset.columns()
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, delimiter=delimiter)
        writer.writeheader()
        if records:
            writer.writerows(records)
    return dataset.with_history("export_csv", path=path, delimiter=delimiter)
