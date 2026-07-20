import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.compiler.compiler import PipelineCompiler, CompilerConfig
from app.compiler.runtime import PythonExecutor


def test_roundtrip_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_data_path = os.path.join(tmpdir, "input.json")
        output_data_path = os.path.join(tmpdir, "output.jsonl")

        # Create sample input dataset
        sample_records = [
            {"id": 1, "text": "Héllo World", "category": "A"},
            {"id": 2, "text": "Café FlowWeaver", "category": "B"}
        ]
        with open(input_data_path, "w", encoding="utf-8") as f:
            json.dump(sample_records, f)

        pipeline = {
            "id": "roundtrip_pipeline",
            "nodes": [
                {
                    "id": "load_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "import_dataset",
                        "title": "Import Input JSON",
                        "params": {"path": input_data_path}
                    }
                },
                {
                    "id": "norm_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "unicode_normalize",
                        "title": "Normalize Text",
                        "params": {"column": "text", "form": "NFC"}
                    }
                },
                {
                    "id": "export_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "write_jsonl",
                        "title": "Export JSONL",
                        "params": {"path": output_data_path}
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "load_1", "target": "norm_1"},
                {"id": "e2", "source": "norm_1", "target": "export_1"}
            ]
        }

        config = CompilerConfig(output_dir=tmpdir, script_name="pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        assert os.path.exists(res.script_path)

        # Execute compiled python script
        exec_res = PythonExecutor.execute_script(res.script_path)
        assert exec_res.success, f"Execution failed with error: {exec_res.stderr}"
        assert os.path.exists(output_data_path)

        with open(output_data_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        assert len(lines) == 2
        assert lines[0]["text"] == "Héllo World"
