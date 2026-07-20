import os
import json
import tempfile
import pytest
from flowweaver.std import (
    Dataset,
    TabularDataset,
    DatasetSchema,
    DatasetMetadata,
    io,
    text,
    tabular,
    dedup,
    utils,
)


def test_dataset_metadata_schema_and_history():
    data = [
        {"id": 1, "name": "Alice", "score": 95.5},
        {"id": 2, "name": "Bob", "score": 88.0}
    ]
    ds = TabularDataset(data)

    # Verify initial schema inferral
    assert len(ds.schema.columns) == 3
    assert ds.schema.names() == ["id", "name", "score"]
    assert ds.metadata.rows == 2
    assert ds.metadata.columns == 3
    assert len(ds.history) == 0

    # Transform dataset and check immutable history tracking
    ds2 = text.lowercase(ds, column="name")
    assert len(ds2.history) == 1
    assert ds2.history[0].name == "lowercase"
    assert ds2.history[0].parameters == {"column": "name"}

    ds3 = tabular.filter_rows(ds2, column="score", operator=">", value=90.0)
    assert len(ds3.history) == 2
    assert ds3.history[1].name == "filter_rows"
    assert ds3.to_list() == [{"id": 1, "name": "alice", "score": 95.5}]


def test_io_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "test.json")
        jsonl_path = os.path.join(tmpdir, "test.jsonl")
        csv_path = os.path.join(tmpdir, "test.csv")
        parquet_path = os.path.join(tmpdir, "test.parquet")

        initial_data = [
            {"code": "A101", "val": 10},
            {"code": "B202", "val": 20}
        ]
        ds = TabularDataset(initial_data)

        # Export JSON
        io.export_json(ds, json_path)
        assert os.path.exists(json_path)

        # Import JSON
        ds_json = io.import_dataset(json_path)
        assert ds_json.to_list() == initial_data
        assert ds_json.history[0].name == "import_dataset"

        # Export & Import JSONL
        io.export_jsonl(ds, jsonl_path)
        assert os.path.exists(jsonl_path)
        ds_jsonl = io.import_dataset(jsonl_path)
        assert ds_jsonl.to_list() == initial_data

        # Export & Import CSV
        io.export_csv(ds, csv_path)
        assert os.path.exists(csv_path)
        ds_csv = io.import_dataset(csv_path)
        assert len(ds_csv.to_list()) == 2

        # Export & Import Parquet
        io.export_parquet(ds, parquet_path)
        assert os.path.exists(parquet_path)
        ds_pq = io.import_dataset(parquet_path)
        assert ds_pq.row_count() == 2


def test_text_operations():
    data = [
        {"title": "  HÉLLO WORLD  ", "tag": "AI"},
        {"title": "FLOWWEAVER", "tag": "ML"}
    ]
    ds = TabularDataset(data)

    ds_lower = text.lowercase(ds, column="title")
    assert ds_lower.to_list()[1]["title"] == "flowweaver"

    ds_upper = text.uppercase(ds, column="tag")
    assert ds_upper.to_list()[0]["tag"] == "AI"

    ds_strip = text.strip_whitespace(ds, column="title")
    assert ds_strip.to_list()[0]["title"] == "HÉLLO WORLD"

    ds_norm = text.unicode_normalize(ds_strip, column="title", form="NFC")
    assert ds_norm.to_list()[0]["title"] == "HÉLLO WORLD"

    ds_regex = text.regex_replace(ds, column="title", pattern=r"\s+", replacement="_")
    assert ds_regex.to_list()[0]["title"] == "_HÉLLO_WORLD_"


def test_tabular_operations():
    data = [
        {"id": 3, "name": "Charlie", "role": "Dev"},
        {"id": 1, "name": "Alice", "role": "Design"},
        {"id": 2, "name": "Bob", "role": "Dev"}
    ]
    ds = TabularDataset(data)

    # Select columns
    ds_sel = tabular.select_columns(ds, columns=["id", "name"])
    assert ds_sel.columns() == ["id", "name"]
    assert "role" not in ds_sel.to_list()[0]

    # Rename columns
    ds_ren = tabular.rename_columns(ds, rename_map={"name": "full_name"})
    assert ds_ren.columns() == ["id", "full_name", "role"]
    assert ds_ren.to_list()[0]["full_name"] == "Charlie"

    # Filter rows
    ds_flt = tabular.filter_rows(ds, column="role", operator="==", value="Dev")
    assert len(ds_flt.to_list()) == 2

    # Sort rows
    ds_srt = tabular.sort_rows(ds, by="id", ascending=True)
    assert [r["id"] for r in ds_srt.to_list()] == [1, 2, 3]


def test_dedup_operations():
    data = [
        {"text": "The quick brown fox jumps over the lazy dog"},
        {"text": "The quick brown fox jumps over the lazy dog"},
        {"text": "the quick brown fox jumps over the lazy dog"},
        {"text": "Something completely different"}
    ]
    ds = TabularDataset(data)

    # Exact deduplication
    ds_exact = dedup.dedup_exact(ds)
    assert len(ds_exact.to_list()) == 3

    # SimHash near-deduplication
    ds_sim = dedup.simhash_deduplicate(ds, column="text", threshold=5)
    assert len(ds_sim.to_list()) == 2


def test_validation_errors():
    ds = TabularDataset([{"a": 1}])

    with pytest.raises(TypeError):
        text.lowercase("not_a_dataset", column="a")

    with pytest.raises(ValueError, match="Column 'non_existent' not found"):
        text.lowercase(ds, column="non_existent")

    with pytest.raises(ValueError, match="Columns \['x', 'y'\] not found"):
        tabular.select_columns(ds, columns=["x", "y"])
