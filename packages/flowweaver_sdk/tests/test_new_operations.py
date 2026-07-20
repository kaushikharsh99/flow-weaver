"""Tests for the new flowweaver.std.tabular operations (M1 expansion)."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flowweaver.std.datasets import TabularDataset
from flowweaver.std.tabular import (
    select_columns,
    rename_columns,
    filter_rows,
    sort_rows,
    drop_columns,
    sample_rows,
    shuffle,
    split_dataset,
    concatenate,
    statistics,
)


def _make_dataset(n=10):
    """Create a test dataset with n rows."""
    rows = [{"id": i, "name": f"item_{i}", "score": i * 10, "category": "A" if i % 2 == 0 else "B"} for i in range(n)]
    return TabularDataset(rows, columns=["id", "name", "score", "category"])


class TestDropColumns:
    def test_drop_single_column(self):
        ds = _make_dataset(5)
        result = drop_columns(ds, columns=["score"])
        assert "score" not in result.columns()
        assert "id" in result.columns()
        assert "name" in result.columns()
        assert len(result.to_list()) == 5

    def test_drop_multiple_columns(self):
        ds = _make_dataset(5)
        result = drop_columns(ds, columns=["score", "category"])
        assert result.columns() == ["id", "name"]

    def test_drop_preserves_data(self):
        ds = _make_dataset(3)
        result = drop_columns(ds, columns=["category"])
        rows = result.to_list()
        assert rows[0]["id"] == 0
        assert rows[0]["name"] == "item_0"
        assert "category" not in rows[0]

    def test_drop_records_history(self):
        ds = _make_dataset(3)
        result = drop_columns(ds, columns=["score"])
        assert any(h.name == "drop_columns" for h in result.history)


class TestSampleRows:
    def test_sample_fewer_than_total(self):
        ds = _make_dataset(100)
        result = sample_rows(ds, n=10, seed=42)
        assert len(result.to_list()) == 10

    def test_sample_deterministic(self):
        ds = _make_dataset(100)
        r1 = sample_rows(ds, n=10, seed=42)
        r2 = sample_rows(ds, n=10, seed=42)
        assert r1.to_list() == r2.to_list()

    def test_sample_different_seeds(self):
        ds = _make_dataset(100)
        r1 = sample_rows(ds, n=10, seed=42)
        r2 = sample_rows(ds, n=10, seed=99)
        # Very likely different
        assert r1.to_list() != r2.to_list()

    def test_sample_more_than_available(self):
        ds = _make_dataset(5)
        result = sample_rows(ds, n=100, seed=42)
        assert len(result.to_list()) == 5


class TestShuffle:
    def test_shuffle_preserves_length(self):
        ds = _make_dataset(20)
        result = shuffle(ds, seed=42)
        assert len(result.to_list()) == 20

    def test_shuffle_deterministic(self):
        ds = _make_dataset(20)
        r1 = shuffle(ds, seed=42)
        r2 = shuffle(ds, seed=42)
        assert r1.to_list() == r2.to_list()

    def test_shuffle_changes_order(self):
        ds = _make_dataset(20)
        result = shuffle(ds, seed=42)
        original_ids = [r["id"] for r in ds.to_list()]
        shuffled_ids = [r["id"] for r in result.to_list()]
        assert shuffled_ids != original_ids  # Very likely to be different


class TestSplitDataset:
    def test_split_ratio(self):
        ds = _make_dataset(100)
        train, test = split_dataset(ds, ratio=0.8, seed=42)
        assert len(train.to_list()) == 80
        assert len(test.to_list()) == 20

    def test_split_preserves_all_rows(self):
        ds = _make_dataset(50)
        train, test = split_dataset(ds, ratio=0.6, seed=42)
        all_ids = sorted([r["id"] for r in train.to_list()] + [r["id"] for r in test.to_list()])
        expected_ids = sorted([r["id"] for r in ds.to_list()])
        assert all_ids == expected_ids

    def test_split_deterministic(self):
        ds = _make_dataset(50)
        t1, v1 = split_dataset(ds, ratio=0.8, seed=42)
        t2, v2 = split_dataset(ds, ratio=0.8, seed=42)
        assert t1.to_list() == t2.to_list()
        assert v1.to_list() == v2.to_list()

    def test_split_invalid_ratio(self):
        ds = _make_dataset(10)
        with pytest.raises(ValueError):
            split_dataset(ds, ratio=1.5)


class TestConcatenate:
    def test_concatenate_same_schema(self):
        ds1 = _make_dataset(5)
        ds2 = _make_dataset(5)
        result = concatenate(ds1, ds2)
        assert len(result.to_list()) == 10

    def test_concatenate_preserves_data(self):
        rows1 = [{"x": 1}, {"x": 2}]
        rows2 = [{"x": 3}, {"x": 4}]
        ds1 = TabularDataset(rows1, columns=["x"])
        ds2 = TabularDataset(rows2, columns=["x"])
        result = concatenate(ds1, ds2)
        vals = [r["x"] for r in result.to_list()]
        assert vals == [1, 2, 3, 4]


class TestStatistics:
    def test_statistics_returns_dataset(self):
        ds = _make_dataset(10)
        result = statistics(ds)
        # Statistics should return a dataset with metadata
        assert result is not None
        assert "statistics" in result.metadata.extra

    def test_statistics_includes_counts(self):
        ds = _make_dataset(10)
        result = statistics(ds)
        stats = result.metadata.extra["statistics"]
        # Should have stats for each column
        assert "id" in stats
        assert stats["id"]["count"] == 10


class TestSortRows:
    def test_sort_ascending(self):
        rows = [{"id": 3, "name": "c"}, {"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        ds = TabularDataset(rows, columns=["id", "name"])
        result = sort_rows(ds, by="id", ascending=True)
        ids = [r["id"] for r in result.to_list()]
        assert ids == [1, 2, 3]

    def test_sort_descending(self):
        rows = [{"id": 3, "name": "c"}, {"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        ds = TabularDataset(rows, columns=["id", "name"])
        result = sort_rows(ds, by="id", ascending=False)
        ids = [r["id"] for r in result.to_list()]
        assert ids == [3, 2, 1]


class TestIntegrationPipeline:
    """Test chaining multiple operations together like a real pipeline."""

    def test_import_shuffle_sample_split(self):
        ds = _make_dataset(100)
        shuffled = shuffle(ds, seed=42)
        sampled = sample_rows(shuffled, n=50, seed=42)
        train, test = split_dataset(sampled, ratio=0.8, seed=42)
        assert len(train.to_list()) == 40
        assert len(test.to_list()) == 10

    def test_select_drop_sort_chain(self):
        ds = _make_dataset(10)
        selected = select_columns(ds, columns=["id", "name", "score"])
        dropped = drop_columns(selected, columns=["score"])
        sorted_ds = sort_rows(dropped, by="id", ascending=False)
        rows = sorted_ds.to_list()
        assert rows[0]["id"] == 9
        assert "score" not in rows[0]
