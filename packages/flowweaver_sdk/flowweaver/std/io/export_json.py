import os
import json
from flowweaver.std.datasets import Dataset
from flowweaver.std.utils.validation import validate_dataset


def export_json(dataset: Dataset, path: str, indent: int = 2) -> Dataset:
    """Exports dataset records into a formatted JSON document."""
    validate_dataset(dataset)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    records = dataset.to_list()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=indent, ensure_ascii=False)
    return dataset.with_history("export_json", path=path, indent=indent)
