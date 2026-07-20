"""
FlowWeaver Standard Library (flowweaver.std)

Pure Python preprocessing operations standard library for dataset engineering.
"""

from flowweaver.std.datasets import (
    Dataset,
    TabularDataset,
    PolarsDataset,
    ArrowDataset,
    StreamingDataset,
    OperationRecord,
    DatasetSchema,
    DatasetMetadata,
)

from flowweaver.std import io
from flowweaver.std import text
from flowweaver.std import tabular
from flowweaver.std import dedup
from flowweaver.std import utils

__all__ = [
    "Dataset",
    "TabularDataset",
    "PolarsDataset",
    "ArrowDataset",
    "StreamingDataset",
    "OperationRecord",
    "DatasetSchema",
    "DatasetMetadata",
    "io",
    "text",
    "tabular",
    "dedup",
    "utils",
]
