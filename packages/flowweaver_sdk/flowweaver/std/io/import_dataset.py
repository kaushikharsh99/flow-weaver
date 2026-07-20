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


def import_dataset(
    path: str,
    format: Optional[str] = None,
    delimiter: str = ",",
    root_key: str = "",
    encoding: str = "utf-8"
) -> Dataset:
    """Universal Dataset Loader. Auto-detects structure and returns a FlowWeaver Dataset instance."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")

    ext = format.lower() if format else os.path.splitext(path)[1].lstrip(".").lower()

    if ext == "json":
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

    elif ext in ("jsonl", "ndjson"):
        rows = []
        with open(path, "r", encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        cols = list(rows[0].keys()) if rows else []
        dataset = TabularDataset(rows, columns=cols)

    elif ext in ("parquet", "pq"):
        try:
            import polars as pl
            df = pl.read_parquet(path)
            dataset = PolarsDataset(df)
        except Exception:
            import pyarrow.parquet as pq
            table = pq.read_table(path)
            dataset = ArrowDataset(table)

    else: # Default to CSV/TSV
        actual_delim = "\t" if ext == "tsv" else delimiter
        rows = []
        with open(path, "r", encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=actual_delim)
            for r in reader:
                rows.append(dict(r))
        cols = list(rows[0].keys()) if rows else []
        dataset = TabularDataset(rows, columns=cols)

    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    classification = _classify_dataset(dataset.columns(), dataset.to_list()[:10])
    dataset.metadata.extra["dataset_type"] = classification["type"]
    dataset.metadata.extra["confidence"] = classification["confidence"]
    dataset.metadata.extra["recommendation"] = classification["recommendation"]
    return dataset.with_history("import_dataset", path=path, format=ext)

