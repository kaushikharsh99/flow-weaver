import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.compiler.compiler import PipelineCompiler, CompilerConfig
from app.compiler.runtime.executor import PythonExecutor
from app.engine.nodes.cleaning import LowercaseNode, UnicodeNormalizeNode, RegexReplaceNode, RemoveEmptyNode
from app.engine.nodes.loaders import LoadCSVNode, LoadJSONLNode
from app.engine.nodes.exports import WriteJSONLNode
from app.engine.nodes.transform import RenameColumnsNode, SelectColumnsNode
from app.engine.nodes.filters import FilterRowsNode, DedupNode


def test_node_compile_methods_directly():
    class DummyContext:
        def __init__(self):
            self.input_var = "dataset"
            self.output_var = "dataset_1"
            self.current_params = {"column": "title", "form": "NFKC"}
            self.imports = set()

        def call(self, func_path, *args, **kwargs):
            self.imports.add(func_path)
            return {"func": func_path, "args": args, "kwargs": kwargs}

    ctx = DummyContext()

    # LowercaseNode compile
    node_lower = LowercaseNode()
    ir_lower = node_lower.compile(ctx)
    assert ir_lower["func"] == "flowweaver.std.text.lowercase"
    assert ir_lower["kwargs"]["column"] == "title"

    # UnicodeNormalizeNode compile
    node_uni = UnicodeNormalizeNode()
    ir_uni = node_uni.compile(ctx)
    assert ir_uni["func"] == "flowweaver.std.text.unicode_normalize"
    assert ir_uni["kwargs"]["form"] == "NFKC"

    # SelectColumnsNode compile
    ctx.current_params = {"columns": "id, title"}
    node_sel = SelectColumnsNode()
    ir_sel = node_sel.compile(ctx)
    assert ir_sel["func"] == "flowweaver.std.tabular.select_columns"
    assert ir_sel["kwargs"]["columns"] == ["id", "title"]


def test_node_migration_end_to_end_compilation_and_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = os.path.join(tmpdir, "input.csv")
        output_jsonl = os.path.join(tmpdir, "output.jsonl")

        with open(input_csv, "w", encoding="utf-8") as f:
            f.write("text,category\n  HÉLLO WORLD  ,A\nFLOWWEAVER  ,B\n")

        pipeline = {
            "id": "migrated_nodes_pipeline",
            "nodes": [
                {
                    "id": "load_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "load_csv",
                        "title": "Load CSV",
                        "params": {"path": input_csv, "delimiter": ","}
                    }
                },
                {
                    "id": "lowercase_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "lowercase",
                        "title": "Lowercase Text",
                        "params": {"column": "text"}
                    }
                },
                {
                    "id": "export_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "write_jsonl",
                        "title": "Write JSONL",
                        "params": {"path": output_jsonl}
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "load_1", "target": "lowercase_1"},
                {"id": "e2", "source": "lowercase_1", "target": "export_1"}
            ]
        }

        config = CompilerConfig(output_dir=tmpdir, script_name="pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        assert "from flowweaver.std.io import import_dataset, export_jsonl" in res.script
        assert "from flowweaver.std.text import lowercase" in res.script
        # Verify NO legacy core_logic imports exist
        assert "app.engine.nodes.core_logic" not in res.script

        # Execute compiled python script
        exec_res = PythonExecutor.execute_script(res.script_path)
        assert exec_res.success, f"Execution failed: {exec_res.stderr}"
        assert os.path.exists(output_jsonl)

        with open(output_jsonl, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        assert len(lines) == 2
        assert lines[0]["text"] == "  héllo world  "
