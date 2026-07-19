import os

sdk_dir = "packages/flowweaver_sdk"

# 1. Overwrite flowweaver/sdk/dataset.py to implement Polars, PyArrow, DuckDB and Streaming datasets
dataset_py = """import abc
from typing import List, Dict, Any, Optional, Iterator

class Dataset(abc.ABC):
    @abc.abstractmethod
    def to_list(self) -> List[Dict[str, Any]]:
        \"\"\"Convert dataset to list of dicts (tabular).\"\"\"
        pass

    @abc.abstractmethod
    def columns(self) -> List[str]:
        \"\"\"Return list of dataset columns.\"\"\"
        pass
        
    @abc.abstractmethod
    def row_count(self) -> Optional[int]:
        \"\"\"Return number of rows if known, or None.\"\"\"
        pass

    def to_polars(self) -> Any:
        \"\"\"Convert dataset to a Polars DataFrame. Loaded lazily.\"\"\"
        import polars as pl
        return pl.DataFrame(self.to_list())

    def to_arrow(self) -> Any:
        \"\"\"Convert dataset to a PyArrow Table. Loaded lazily.\"\"\"
        import pyarrow as pa
        return pa.Table.from_pydict({
            col: [row.get(col) for row in self.to_list()]
            for col in self.columns()
        })

    def iter_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        \"\"\"Iterate over dataset records in chunk batches (streaming).\"\"\"
        data = self.to_list()
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]


class TabularDataset(Dataset):
    \"\"\"Standard in-memory list-of-dicts tabular dataset.\"\"\"
    def __init__(self, data: List[Dict[str, Any]], columns: Optional[List[str]] = None):
        self._data = data
        if columns is not None:
            self._columns = columns
        else:
            self._columns = list(data[0].keys()) if data else []
        
    def to_list(self) -> List[Dict[str, Any]]:
        return self._data
        
    def columns(self) -> List[str]:
        return self._columns
        
    def row_count(self) -> Optional[int]:
        return len(self._data)


class PolarsDataset(Dataset):
    \"\"\"Dataset wrapper around a Polars DataFrame.\"\"\"
    def __init__(self, df: Any):
        self.df = df

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
        # Process polars df chunk-by-chunk using slices
        for i in range(0, self.df.height, chunk_size):
            yield self.df.slice(i, chunk_size).to_dicts()


class ArrowDataset(Dataset):
    \"\"\"Dataset wrapper around a PyArrow Table.\"\"\"
    def __init__(self, table: Any):
        self.table = table

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
        # Process PyArrow table by record batches
        for batch in self.table.to_batches(max_chunksize=chunk_size):
            import pyarrow as pa
            yield pa.Table.from_batches([batch]).to_pylist()


class StreamingDataset(Dataset):
    \"\"\"Memory-efficient streaming dataset that wraps an iterator/generator.\"\"\"
    def __init__(self, generator_fn: Any, columns: List[str], estimated_row_count: Optional[int] = None):
        self.generator_fn = generator_fn
        self._columns = columns
        self._estimated_row_count = estimated_row_count

    def to_list(self) -> List[Dict[str, Any]]:
        # Consume full iterator into memory list
        return list(self.iter_records())

    def columns(self) -> List[str]:
        return self._columns

    def row_count(self) -> Optional[int]:
        return self._estimated_row_count

    def iter_records(self) -> Iterator[Dict[str, Any]]:
        \"\"\"Generator yielding records one by one.\"\"\"
        for chunk in self.generator_fn():
            for record in chunk:
                yield record

    def iter_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        \"\"\"Yield batches of chunks directly from the generator iterator.\"\"\"
        current_chunk = []
        for record in self.iter_records():
            current_chunk.append(record)
            if len(current_chunk) >= chunk_size:
                yield current_chunk
                current_chunk = []
        if current_chunk:
            yield current_chunk
"""
with open(f"{sdk_dir}/flowweaver/sdk/dataset.py", "w") as f:
    f.write(dataset_py)

# 2. Update setup.py to include extras_require for data engines
setup_py = """from setuptools import setup, find_packages

setup(
    name="flowweaver-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_packages=["pydantic>=2.0.0"],
    extras_require={
        "polars": ["polars>=1.0.0"],
        "arrow": ["pyarrow>=14.0.0"],
        "duckdb": ["duckdb>=0.9.0"],
    },
    author="FlowWeaver Team",
    description="Core developer SDK for writing FlowWeaver nodes and plugins",
    python_requires=">=3.8",
)
"""
with open(f"{sdk_dir}/setup.py", "w") as f:
    f.write(setup_py)

# 3. Update apps/api/requirements.txt to declare polars, pyarrow, duckdb dependencies
requirements_path = "apps/api/requirements.txt"
requirements_content = """fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.31
pydantic==2.7.4
pydantic-settings==2.3.4
websockets==12.0
python-multipart==0.0.9
polars==1.0.0
pyarrow==16.1.0
duckdb==1.0.0
"""
with open(requirements_path, "w") as f:
    f.write(requirements_content)

print("Scaffolding Data Engine configurations completed successfully!")
