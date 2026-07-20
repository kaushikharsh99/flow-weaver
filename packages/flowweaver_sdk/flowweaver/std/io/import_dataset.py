import os
import json
import csv
from typing import Optional, Dict, Any, List
from flowweaver.std.datasets import Dataset, TabularDataset, PolarsDataset, ArrowDataset, DatasetMetadata


def _classify_dataset(cols: List[str], records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Auto-classifies dataset type and returns confidence stats."""
    cols_set = set(c.lower() for c in cols)
    
    if {"instruction", "output"}.issubset(cols_set) or {"prompt", "response"}.issubset(cols_set):
        return {"type": "Instruction Tuning", "confidence": 0.98, "recommendation": "Unicode Normalize -> Lowercase Instructions -> Filter Empty"}
    elif "messages" in cols_set or "conversations" in cols_set:
        return {"type": "Multi-turn Chat", "confidence": 0.95, "recommendation": "Strip HTML -> SimHash Dedup -> Export Parquet"}
    elif any(c in cols_set for c in ("text", "content", "body", "document", "story", "raw_text")):
        return {"type": "Unstructured Text", "confidence": 0.92, "recommendation": "Unicode NFC -> Regex Replace -> Length Filter -> Export JSONL"}
    else:
        return {"type": "Tabular Data", "confidence": 0.85, "recommendation": "Remove Nulls -> Dedup Exact -> Export Parquet"}


def import_csv_dataset(
    path: str,
    delimiter: str = ",",
    encoding: str = "utf-8"
) -> TabularDataset:
    """Read a CSV/TSV file into a TabularDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    rows = []
    with open(path, "r", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for r in reader:
            rows.append(dict(r))
    cols = list(rows[0].keys()) if rows else []
    dataset = TabularDataset(rows, columns=cols)
    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    return dataset.with_history("import_csv_dataset", path=path, delimiter=delimiter)


def import_json_dataset(
    path: str,
    root_key: str = "",
    encoding: str = "utf-8"
) -> TabularDataset:
    """Parse a JSON file into a TabularDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    with open(path, "r", encoding=encoding) as f:
        data = json.load(f)
    if isinstance(data, dict):
        if root_key and root_key in data and isinstance(data[root_key], list):
            data = data[root_key]
        else:
            for k in ("data", "items", "records", "stories", "train", "documents"):
                if k in data and isinstance(data[k], list):
                    data = data[k]
                    break
    if not isinstance(data, list):
        data = [data]
    cols = list(data[0].keys()) if data and isinstance(data[0], dict) else []
    dataset = TabularDataset(data, columns=cols)
    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    return dataset.with_history("import_json_dataset", path=path, root_key=root_key)


def import_jsonl_dataset(
    path: str,
    encoding: str = "utf-8"
) -> TabularDataset:
    """Parse a JSON Lines file into a TabularDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    rows = []
    with open(path, "r", encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    cols = list(rows[0].keys()) if rows else []
    dataset = TabularDataset(rows, columns=cols)
    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    return dataset.with_history("import_jsonl_dataset", path=path)


def import_parquet_dataset(path: str) -> Dataset:
    """Load a Parquet dataset into a PolarsDataset or ArrowDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    try:
        import polars as pl
        df = pl.read_parquet(path)
        dataset = PolarsDataset(df)
    except Exception:
        import pyarrow.parquet as pq
        table = pq.read_table(path)
        dataset = ArrowDataset(table)
    dataset.metadata.source = path
    return dataset.with_history("import_parquet_dataset", path=path)


def import_dataset(
    path: str,
    format: Optional[str] = None,
    delimiter: str = ",",
    root_key: str = "",
    encoding: str = "utf-8"
) -> Dataset:
    """Universal Dataset Loader. Delegates to format-specific loaders."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")

    ext = format.lower() if format else os.path.splitext(path)[1].lstrip(".").lower()

    if ext == "json":
        dataset = import_json_dataset(path, root_key=root_key, encoding=encoding)
    elif ext in ("jsonl", "ndjson"):
        dataset = import_jsonl_dataset(path, encoding=encoding)
    elif ext in ("parquet", "pq"):
        dataset = import_parquet_dataset(path)
    else:
        actual_delim = "\t" if ext == "tsv" else delimiter
        dataset = import_csv_dataset(path, delimiter=actual_delim, encoding=encoding)

    classification = _classify_dataset(dataset.columns(), dataset.to_list()[:10])
    dataset.metadata.extra["dataset_type"] = classification["type"]
    dataset.metadata.extra["confidence"] = classification["confidence"]
    dataset.metadata.extra["recommendation"] = classification["recommendation"]
    return dataset
