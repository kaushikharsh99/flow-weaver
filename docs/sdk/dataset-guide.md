# FlowWeaver Dataset SDK Guide

FlowWeaver nodes exchange data via structured **Dataset** objects. Returning generic python dicts or lists directly is discouraged as it prevents memory optimizations, typing safety, and unified inspection in the UI.

---

## Dataset Classes

The FlowWeaver SDK provides several classes optimized for different storage backends and sizes:

### 1. `TabularDataset`
Best for standard, small-to-medium memory operations. Wraps a list of python dictionaries.

```python
from flowweaver.sdk import TabularDataset

# Instantiation
data = [
    {"id": 1, "name": "Alice", "role": "Admin"},
    {"id": 2, "name": "Bob", "role": "User"}
]
dataset = TabularDataset(data, columns=["id", "name", "role"])

# Methods
print(dataset.columns())      # ['id', 'name', 'role']
print(dataset.to_list())      # Returns list of dicts
print(len(dataset))           # Returns row count (2)
```

### 2. `PolarsDataset`
Optimized for high-performance memory execution. Wraps a `polars.DataFrame` or `polars.LazyFrame`.
- Uses vectorized operations.
- Ideal for complex transforms (joins, aggregations, fuzzy deduping).

### 3. `ArrowDataset`
Wraps an Apache Arrow `Table` for cross-language sharing and zero-copy memory transport.

### 4. `StreamingDataset`
An iterator-based dataset wrapper for parsing extremely large files (e.g. gigabytes of logs or CSVs) in chunks without loading them entirely into RAM.

---

## Returning Datasets from Nodes

Always wrap execution outputs in a `Dataset` subclass when sending structured data between ports:

```python
# GOOD: Returning structured dataset
return {"out": TabularDataset(processed_rows, columns=columns)}

# BAD: Returning raw lists or dicts
return {"out": processed_rows}
```

---

## Best Practices
- **Column Schema Invariance**: Always specify the `columns` list explicitly when instantiating `TabularDataset` so downstream nodes can map schemas before runtime.
- **Lazy Evaluation**: When using `PolarsDataset`, favor returning lazy query plans (`LazyFrame`) to allow FlowWeaver's compiler to optimize the global execution graph.
