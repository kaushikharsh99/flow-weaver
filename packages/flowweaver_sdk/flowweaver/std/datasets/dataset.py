import abc
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator
from flowweaver.std.datasets.metadata import DatasetMetadata
from flowweaver.std.datasets.schema import DatasetSchema


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
    def __init__(
        self,
        metadata: Optional[DatasetMetadata] = None,
        schema: Optional[DatasetSchema] = None,
        history: Optional[List[OperationRecord]] = None
    ):
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

    def to_polars(self) -> Any:
        """Convert dataset to a Polars DataFrame. Loaded lazily."""
        import polars as pl
        return pl.DataFrame(self.to_list())

    def to_arrow(self) -> Any:
        """Convert dataset to a PyArrow Table. Loaded lazily."""
        import pyarrow as pa
        data = self.to_list()
        cols = self.columns()
        if not data:
            return pa.Table.from_pydict({c: [] for c in cols})
        return pa.Table.from_pydict({
            col: [row.get(col) for row in data]
            for col in cols
        })

    def iter_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        """Iterate over dataset records in chunk batches (streaming)."""
        data = self.to_list()
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def with_history(self, op_name: str, **parameters: Any) -> "Dataset":
        """Appends an operation record to dataset history and returns self."""
        rec = OperationRecord(name=op_name, timestamp=time.time(), parameters=parameters)
        self._history.append(rec)
        return self


class TabularDataset(Dataset):
    """Standard in-memory list-of-dicts tabular dataset."""
    def __init__(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        metadata: Optional[DatasetMetadata] = None,
        schema: Optional[DatasetSchema] = None,
        history: Optional[List[OperationRecord]] = None
    ):
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
    def __init__(
        self,
        df: Any,
        metadata: Optional[DatasetMetadata] = None,
        schema: Optional[DatasetSchema] = None,
        history: Optional[List[OperationRecord]] = None
    ):
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

    def to_polars(self) -> Any:
        return self.df

    def to_arrow(self) -> Any:
        return self.df.to_arrow()

    def iter_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        for i in range(0, self.df.height, chunk_size):
            yield self.df.slice(i, chunk_size).to_dicts()


class ArrowDataset(Dataset):
    """Dataset wrapper around a PyArrow Table."""
    def __init__(
        self,
        table: Any,
        metadata: Optional[DatasetMetadata] = None,
        schema: Optional[DatasetSchema] = None,
        history: Optional[List[OperationRecord]] = None
    ):
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

    def to_polars(self) -> Any:
        import polars as pl
        return pl.from_arrow(self.table)

    def to_arrow(self) -> Any:
        return self.table

    def iter_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        import pyarrow as pa
        for batch in self.table.to_batches(max_chunksize=chunk_size):
            yield pa.Table.from_batches([batch]).to_pylist()


class StreamingDataset(Dataset):
    """Memory-efficient streaming dataset that wraps an iterator/generator."""
    def __init__(
        self,
        generator_fn: Any,
        columns: List[str],
        estimated_row_count: Optional[int] = None,
        metadata: Optional[DatasetMetadata] = None,
        schema: Optional[DatasetSchema] = None,
        history: Optional[List[OperationRecord]] = None
    ):
        super().__init__(metadata=metadata, schema=schema, history=history)
        self.generator_fn = generator_fn
        self._columns = columns
        self._estimated_row_count = estimated_row_count
        self._metadata.rows = estimated_row_count
        self._metadata.columns = len(columns)

    def to_list(self) -> List[Dict[str, Any]]:
        return list(self.iter_records())

    def columns(self) -> List[str]:
        return self._columns

    def row_count(self) -> Optional[int]:
        return self._estimated_row_count

    def iter_records(self) -> Iterator[Dict[str, Any]]:
        for chunk in self.generator_fn():
            for record in chunk:
                yield record

    def iter_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        current_chunk = []
        for record in self.iter_records():
            current_chunk.append(record)
            if len(current_chunk) >= chunk_size:
                yield current_chunk
                current_chunk = []
        if current_chunk:
            yield current_chunk
