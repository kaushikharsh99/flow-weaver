"""
FlowWeaver Generated Preprocessing Script
Pipeline: yuc6u19c
Generated: 2026-07-20 08:28:47 UTC

This script was compiled from a visual FlowWeaver pipeline.
It is fully standalone and can be run with: python yuc6u19c.py
"""


import abc
import argparse
import csv
import json
import logging
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

# ======================================================
# Core Dataset Engineering Classes
# ======================================================
@dataclass
class ColumnSchema:
    """Represents the schema definition of a dataset column."""
    name: str
    data_type: str = 'string'
    nullable: bool = True

@dataclass
class DatasetSchema:
    """Represents the overall schema of a Dataset."""
    columns: List[ColumnSchema] = field(default_factory=list)

    @classmethod
    def infer_from_records(cls, records: List[Dict[str, Any]]) -> 'DatasetSchema':
        if not records:
            return cls()
        cols = []
        sample_row = records[0]
        for name, val in sample_row.items():
            dtype = 'string'
            if isinstance(val, bool):
                dtype = 'boolean'
            elif isinstance(val, int):
                dtype = 'integer'
            elif isinstance(val, float):
                dtype = 'float'
            elif isinstance(val, (list, tuple)):
                dtype = 'array'
            elif isinstance(val, dict):
                dtype = 'struct'
            cols.append(ColumnSchema(name=name, data_type=dtype, nullable=val is None))
        return cls(columns=cols)

@dataclass
class DatasetMetadata:
    """Stores metadata information for a Dataset instance."""
    rows: Optional[int] = None
    columns: int = 0
    memory_bytes: Optional[int] = None
    source: Optional[str] = None
    encoding: str = 'utf-8'
    created_at: float = field(default_factory=time.time)
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OperationRecord:
    """Record of an operation executed on a dataset."""
    name: str
    timestamp: float = field(default_factory=time.time)
    parameters: Dict[str, Any] = field(default_factory=dict)

class Dataset(abc.ABC):
    """Core FlowWeaver immutable Dataset abstraction.
    
    Wraps tabular dicts, Polars DataFrames, or PyArrow Tables while maintaining
    Schema, Metadata, and Operation History tracking.
    """

    def __init__(self, metadata: Optional[DatasetMetadata]=None, schema: Optional[DatasetSchema]=None, history: Optional[List[OperationRecord]]=None):
        self._metadata = metadata or DatasetMetadata()
        self._schema = schema or DatasetSchema()
        self._history = list(history) if history else []

    @property
    def metadata(self) -> DatasetMetadata:
        return self._metadata

    @property
    def schema(self) -> DatasetSchema:
        return self._schema

    @property
    def history(self) -> List[OperationRecord]:
        return list(self._history)

    @abc.abstractmethod
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert dataset to list of dicts (tabular)."""
        pass

    @abc.abstractmethod
    def columns(self) -> List[str]:
        """Return list of dataset columns."""
        pass

    @abc.abstractmethod
    def row_count(self) -> Optional[int]:
        """Return number of rows if known, or None."""
        pass

    def nulls(self) -> Dict[str, int]:
        """Calculates missing/null count for each column."""
        records = self.to_list()
        cols = self.columns()
        null_map = {c: 0 for c in cols}
        for r in records:
            for c in cols:
                val = r.get(c)
                if val is None or str(val).strip() == '':
                    null_map[c] += 1
        return null_map

    def memory(self) -> int:
        """Estimates dataset memory usage in bytes."""
        import sys
        records = self.to_list()
        return sum((sys.getsizeof(r) + sum((sys.getsizeof(k) + sys.getsizeof(v) for k, v in r.items())) for r in records)) if records else 0

    def to_arrow(self) -> Any:
        """Convert dataset to a PyArrow Table. Loaded lazily."""
        import pyarrow as pa
        data = self.to_list()
        cols = self.columns()
        if not data:
            return pa.Table.from_pydict({c: [] for c in cols})
        return pa.Table.from_pydict({col: [row.get(col) for row in data] for col in cols})

    def iter_chunks(self, chunk_size: int=1000) -> Iterator[List[Dict[str, Any]]]:
        """Iterate over dataset records in chunk batches (streaming)."""
        data = self.to_list()
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def with_history(self, op_name: str, **parameters: Any) -> 'Dataset':
        """Appends an operation record to dataset history and returns self."""
        rec = OperationRecord(name=op_name, timestamp=time.time(), parameters=parameters)
        self._history.append(rec)
        return self

class TabularDataset(Dataset):
    """Standard in-memory list-of-dicts tabular dataset."""

    def __init__(self, data: List[Dict[str, Any]], columns: Optional[List[str]]=None, metadata: Optional[DatasetMetadata]=None, schema: Optional[DatasetSchema]=None, history: Optional[List[OperationRecord]]=None):
        super().__init__(metadata=metadata, schema=schema, history=history)
        self._data = data
        if columns is not None:
            self._columns = columns
        else:
            self._columns = list(data[0].keys()) if data else []
        if not self._schema.columns:
            self._schema = DatasetSchema.infer_from_records(data)
        self._metadata.rows = len(data)
        self._metadata.columns = len(self._columns)

    def to_list(self) -> List[Dict[str, Any]]:
        return self._data

    def columns(self) -> List[str]:
        return self._columns

    def row_count(self) -> Optional[int]:
        return len(self._data)

class PolarsDataset(Dataset):
    """Dataset wrapper around a Polars DataFrame."""

    def __init__(self, df: Any, metadata: Optional[DatasetMetadata]=None, schema: Optional[DatasetSchema]=None, history: Optional[List[OperationRecord]]=None):
        super().__init__(metadata=metadata, schema=schema, history=history)
        self.df = df
        self._metadata.rows = df.height
        self._metadata.columns = len(df.columns)

    def to_list(self) -> List[Dict[str, Any]]:
        return self.df.to_dicts()

    def columns(self) -> List[str]:
        return self.df.columns

    def row_count(self) -> Optional[int]:
        return self.df.height

    def to_arrow(self) -> Any:
        return self.df.to_arrow()

    def iter_chunks(self, chunk_size: int=1000) -> Iterator[List[Dict[str, Any]]]:
        for i in range(0, self.df.height, chunk_size):
            yield self.df.slice(i, chunk_size).to_dicts()

class ArrowDataset(Dataset):
    """Dataset wrapper around a PyArrow Table."""

    def __init__(self, table: Any, metadata: Optional[DatasetMetadata]=None, schema: Optional[DatasetSchema]=None, history: Optional[List[OperationRecord]]=None):
        super().__init__(metadata=metadata, schema=schema, history=history)
        self.table = table
        self._metadata.rows = table.num_rows
        self._metadata.columns = len(table.column_names)

    def to_list(self) -> List[Dict[str, Any]]:
        return self.table.to_pylist()

    def columns(self) -> List[str]:
        return self.table.column_names

    def row_count(self) -> Optional[int]:
        return self.table.num_rows

    def to_arrow(self) -> Any:
        return self.table

    def iter_chunks(self, chunk_size: int=1000) -> Iterator[List[Dict[str, Any]]]:
        import pyarrow as pa
        for batch in self.table.to_batches(max_chunksize=chunk_size):
            yield pa.Table.from_batches([batch]).to_pylist()

# ======================================================
# Helper Validation & Instrumentation Utilities
# ======================================================
def validate_dataset(dataset: Any) -> Dataset:
    """Ensures input is a valid FlowWeaver Dataset instance."""
    if not isinstance(dataset, Dataset):
        raise TypeError(f'Expected input to be an instance of flowweaver.std.Dataset, got {type(dataset).__name__}')
    return dataset

def validate_column_exists(dataset: Dataset, column: str) -> None:
    """Ensures the specified column exists in the dataset."""
    cols = dataset.columns()
    if column not in cols:
        raise ValueError(f"Column '{column}' not found in dataset columns: {cols}")

# ======================================================
# Pipeline Standard Operations
# ======================================================
def import_dataset(path: str, format: Optional[str]=None, delimiter: str=',', root_key: str='', encoding: str='utf-8') -> Dataset:
    """Universal Dataset Loader. Delegates to format-specific loaders."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'Dataset file not found: {path}')
    ext = format.lower() if format else os.path.splitext(path)[1].lstrip('.').lower()
    if ext == 'json':
        return import_json_dataset(path, root_key=root_key, encoding=encoding)
    elif ext in ('jsonl', 'ndjson'):
        return import_jsonl_dataset(path, encoding=encoding)
    elif ext in ('parquet', 'pq'):
        return import_parquet_dataset(path)
    else:
        actual_delim = '\t' if ext == 'tsv' else delimiter
        return import_csv_dataset(path, delimiter=actual_delim, encoding=encoding)

def unicode_normalize(dataset: Dataset, column: str, form: str='NFC') -> Dataset:
    """Applies Unicode normalization (NFC, NFD, NFKC, NFKD) to values in target column."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)
    valid_forms = ('NFC', 'NFD', 'NFKC', 'NFKD')
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
    res = TabularDataset(new_rows, columns=dataset.columns(), metadata=dataset.metadata, history=dataset.history)
    return res.with_history('unicode_normalize', column=column, form=form)

def regex_replace(dataset: Dataset, column: str, pattern: str, replacement: str) -> Dataset:
    """Performs regular expression search-and-replace on target column values."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)
    compiled_re = re.compile(pattern)
    rows = dataset.to_list()
    new_rows = []
    for r in rows:
        row_copy = dict(r)
        val = row_copy.get(column)
        if val is not None:
            row_copy[column] = compiled_re.sub(replacement, str(val))
        new_rows.append(row_copy)
    res = TabularDataset(new_rows, columns=dataset.columns(), metadata=dataset.metadata, history=dataset.history)
    return res.with_history('regex_replace', column=column, pattern=pattern, replacement=replacement)

def export_jsonl(dataset: Dataset, path: str) -> Dataset:
    """Exports dataset records into a JSON Lines (.jsonl) document."""
    validate_dataset(dataset)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    records = dataset.to_list()
    with open(path, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return dataset.with_history('export_jsonl', path=path)

def import_json_dataset(path: str, root_key: str='', encoding: str='utf-8') -> TabularDataset:
    """Parse a JSON file into a TabularDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'Dataset file not found: {path}')
    with open(path, 'r', encoding=encoding) as f:
        data = json.load(f)
    if isinstance(data, dict):
        if root_key and root_key in data and isinstance(data[root_key], list):
            data = data[root_key]
        else:
            for k in ('data', 'items', 'records', 'stories', 'train', 'documents'):
                if k in data and isinstance(data[k], list):
                    data = data[k]
                    break
    if not isinstance(data, list):
        data = [data]
    cols = list(data[0].keys()) if data and isinstance(data[0], dict) else []
    dataset = TabularDataset(data, columns=cols)
    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    return dataset.with_history('import_json_dataset', path=path, root_key=root_key)

def import_parquet_dataset(path: str) -> Dataset:
    """Load a Parquet dataset into a PolarsDataset or ArrowDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'Dataset file not found: {path}')
    try:
        import polars as pl
        df = pl.read_parquet(path)
        dataset = PolarsDataset(df)
    except Exception:
        import pyarrow.parquet as pq
        table = pq.read_table(path)
        dataset = ArrowDataset(table)
    dataset.metadata.source = path
    return dataset.with_history('import_parquet_dataset', path=path)

def import_csv_dataset(path: str, delimiter: str=',', encoding: str='utf-8') -> TabularDataset:
    """Read a CSV/TSV file into a TabularDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'Dataset file not found: {path}')
    rows = []
    with open(path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for r in reader:
            rows.append(dict(r))
    cols = list(rows[0].keys()) if rows else []
    dataset = TabularDataset(rows, columns=cols)
    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    return dataset.with_history('import_csv_dataset', path=path, delimiter=delimiter)

def import_jsonl_dataset(path: str, encoding: str='utf-8') -> TabularDataset:
    """Parse a JSON Lines file into a TabularDataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'Dataset file not found: {path}')
    rows = []
    with open(path, 'r', encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    cols = list(rows[0].keys()) if rows else []
    dataset = TabularDataset(rows, columns=cols)
    dataset.metadata.source = path
    dataset.metadata.encoding = encoding
    return dataset.with_history('import_jsonl_dataset', path=path)


# --------------------------------------------------------
# Logging Configuration
# --------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("flowweaver.pipeline")


def parse_args():
    parser = argparse.ArgumentParser(description="Yuc6U19C — FlowWeaver Pipeline")
    parser.add_argument("--input", default="data/TinyStories_all_data", help="Input dataset path")
    parser.add_argument("--output", default="out/tinystories_prep.jsonl", help="Output file path")
    parser.add_argument("--dry-run", action="store_true", help="Validate pipeline without writing output")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting pipeline: yuc6u19c")
    pipeline_start = time.time()

    # --------------------------------------------------------
    # Step 1/4: Import Dataset
    # --------------------------------------------------------
    logger.info("Step 1/4: Import Dataset")
    raw_dataset = import_dataset(path='/run/media/harsh/STORAGE/Tiny-Stories-Original/TinyStories_all_data')

    # --------------------------------------------------------
    # Step 2/4: Apply Unicode Normalization
    # --------------------------------------------------------
    logger.info("Step 2/4: Apply Unicode Normalization")
    normalized_dataset = unicode_normalize(raw_dataset, column='story', form='NFC')

    # --------------------------------------------------------
    # Step 3/4: Apply Regex Text Replacement
    # --------------------------------------------------------
    logger.info("Step 3/4: Apply Regex Text Replacement")
    cleaned_dataset = regex_replace(normalized_dataset, column='story', pattern='\\s+', replacement=' ')

    # --------------------------------------------------------
    # Step 4/4: Export to JSON Lines
    # --------------------------------------------------------
    logger.info("Step 4/4: Export to JSON Lines")
    if not args.dry_run:
        export_jsonl(cleaned_dataset, path=args.output)
    else:
        logger.info("[Dry Run] Skipped export: export_jsonl(cleaned_dataset, path=args.output)")

    elapsed = time.time() - pipeline_start
    logger.info(f"Pipeline completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()

