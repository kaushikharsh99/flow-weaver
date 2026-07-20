import os
import json
from flowweaver.std.datasets import Dataset
from flowweaver.std.utils.validation import validate_dataset


def export_jsonl(dataset: Dataset, path: str) -> Dataset:
    """Exports dataset records into a JSON Lines (.jsonl) document."""
    validate_dataset(dataset)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    records = dataset.to_list()
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return dataset.with_history("export_jsonl", path=path)
