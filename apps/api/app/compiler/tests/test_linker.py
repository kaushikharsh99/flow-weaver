import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.compiler.compiler import PipelineCompiler, CompilerConfig
from app.compiler.linker import PipelineLinker
from app.compiler.runtime.executor import PythonExecutor


def test_linker_tree_shaking_and_dead_code_elimination():
    linker = PipelineLinker()
    # Link only simple tabular operations
    code, reqs = linker.link(["lowercase", "filter_rows", "export_csv"])

    # 1. Verify reachable dataset classes are included
    assert "class Dataset" in code
    assert "class TabularDataset" in code

    # 2. Verify unused dataset implementations are excluded (tree shaking)
    assert "class StreamingDataset" not in code
    assert "class PolarsDataset" not in code
    assert "class ArrowDataset" not in code

    # 3. Verify unreferenced helpers are excluded
    assert "def simhash_deduplicate" not in code
    assert "class ProgressTracker" not in code

    # 4. Verify unreferenced class methods are pruned
    assert "def to_polars(" not in code
    assert "def to_arrow(" not in code
    assert "def save(" not in code

    # 5. Verify no third-party package requirements detected for standard operations
    assert reqs == []


def test_linker_import_deduplication_and_grouping():
    linker = PipelineLinker()
    code, _ = linker.link(["unicode_normalize", "regex_replace", "export_jsonl"])

    # Ensure stdlib imports are grouped cleanly and not duplicated
    import_lines = [line for line in code.splitlines() if line.startswith("import ") or line.startswith("from ")]
    assert len(import_lines) == len(set(import_lines)), "Imports should be deduplicated"
    
    # Ensure flowweaver internal imports are removed
    for line in import_lines:
        assert not line.startswith("from flowweaver"), f"Internal import '{line}' should be removed in linked code"


def test_standalone_executable_script_size_reduction():
    pipeline = {
        "id": "compact_pipeline",
        "nodes": [
            {
                "id": "n1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "import_dataset",
                    "title": "Import CSV",
                    "params": {"path": "sample.csv"}
                }
            },
            {
                "id": "n2",
                "type": "pipelineNode",
                "data": {
                    "typeId": "dedup_exact",
                    "title": "Exact Dedup",
                    "params": {}
                }
            },
            {
                "id": "n3",
                "type": "pipelineNode",
                "data": {
                    "typeId": "write_csv",
                    "title": "Write CSV",
                    "params": {"path": "out.csv"}
                }
            }
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"}
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config = CompilerConfig(output_dir=tmpdir, script_name="compact_pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        # Verify script size is compact (< 300 LOC)
        lines = res.script.splitlines()
        assert len(lines) < 450, f"Generated script size too large: {len(lines)} lines"
        assert "class StreamingDataset" not in res.script


def test_terminal_export_and_format_specific_loader():
    pipeline = {
        "id": "json_pipeline",
        "nodes": [
            {
                "id": "n1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "import_dataset",
                    "title": "Import JSON",
                    "params": {"path": "data.json"}
                }
            },
            {
                "id": "n2",
                "type": "pipelineNode",
                "data": {
                    "typeId": "dedup_exact",
                    "title": "Exact Dedup",
                    "params": {}
                }
            },
            {
                "id": "n3",
                "type": "pipelineNode",
                "data": {
                    "typeId": "write_jsonl",
                    "title": "Export JSONL",
                    "params": {"path": "out.jsonl"}
                }
            }
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"}
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config = CompilerConfig(output_dir=tmpdir, script_name="json_pipe.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        code = res.script

        # 1. Format specific loader emitted
        assert "def import_json_dataset" in code
        assert "raw_dataset = import_json_dataset" in code

        # 2. Terminal export node has no variable assignment
        assert "export_jsonl(deduplicated_dataset, path=" in code
        assert "processed_dataset = export_jsonl" not in code

        # 3. Unused dataset classes excluded
        assert "class PolarsDataset" not in code
        assert "class ArrowDataset" not in code
        assert "class StreamingDataset" not in code
