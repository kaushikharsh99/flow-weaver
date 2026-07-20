import os
from flowweaver.std.datasets import Dataset
from flowweaver.std.utils.validation import validate_dataset


def export_parquet(dataset: Dataset, path: str) -> Dataset:
    """Exports dataset records into a Parquet binary document using Polars or PyArrow."""
    validate_dataset(dataset)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        df = dataset.to_polars()
        df.write_parquet(path)
    except Exception:
        import pyarrow.parquet as pq
        table = dataset.to_arrow()
        pq.write_table(table, path)
    return dataset.with_history("export_parquet", path=path)
