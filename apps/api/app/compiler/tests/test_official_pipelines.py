import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.compiler.compiler import PipelineCompiler, CompilerConfig
from app.compiler.runtime.executor import PythonExecutor


def test_official_tinystories_pipeline_compilation_and_execution():
    template_path = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "tpl_tinystories.json")
    with open(template_path, "r", encoding="utf-8") as f:
        pipeline = json.load(f)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_data = os.path.join(tmpdir, "tinystories.json")
        output_jsonl = os.path.join(tmpdir, "out", "tinystories_prep.jsonl")

        sample_stories = [
            {"story": "  Once upon a time, there was a little robot.  "},
            {"story": "The robot loved to compile Python code!  "}
        ]
        with open(input_data, "w", encoding="utf-8") as f:
            json.dump(sample_stories, f)

        # Override path parameter to point to temporary input file
        pipeline["nodes"][0]["data"]["params"]["path"] = input_data
        pipeline["nodes"][3]["data"]["params"]["path"] = output_jsonl

        config = CompilerConfig(output_dir=tmpdir, script_name="tinystories_pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        assert "raw_dataset = import_json_dataset" in res.script
        assert "normalized_dataset = unicode_normalize(raw_dataset, column='story', form='NFC')" in res.script
        assert "cleaned_dataset = regex_replace(normalized_dataset, column='story', pattern='\\\\s+', replacement=' ')" in res.script
        assert "export_jsonl(cleaned_dataset, path=" in res.script

        # Execute compiled python script
        exec_res = PythonExecutor.execute_script(res.script_path)
        assert exec_res.success, f"Execution failed: {exec_res.stderr}"
        assert os.path.exists(output_jsonl)

        with open(output_jsonl, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 2
        assert lines[0]["story"] == " Once upon a time, there was a little robot. "


def test_official_alpaca_pipeline_compilation_and_execution():
    template_path = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "tpl_alpaca_instruction.json")
    with open(template_path, "r", encoding="utf-8") as f:
        pipeline = json.load(f)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_data = os.path.join(tmpdir, "alpaca.json")
        output_jsonl = os.path.join(tmpdir, "out", "alpaca_finetune.jsonl")

        sample_alpaca = [
            {"instruction": "WRITE A PYTHON FUNCTION.", "input": "", "output": "def foo(): pass"},
            {"instruction": "WRITE A PYTHON FUNCTION.", "input": "", "output": "def foo(): pass"}, # Duplicate
            {"instruction": "   ", "input": "", "output": ""} # Empty
        ]
        with open(input_data, "w", encoding="utf-8") as f:
            json.dump(sample_alpaca, f)

        pipeline["nodes"][0]["data"]["params"]["path"] = input_data
        pipeline["nodes"][4]["data"]["params"]["path"] = output_jsonl

        config = CompilerConfig(output_dir=tmpdir, script_name="alpaca_pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        assert "raw_dataset = import_json_dataset" in res.script
        assert "normalized_dataset = lowercase(raw_dataset, column='instruction')" in res.script
        assert "deduplicated_dataset = dedup_exact(filtered_dataset)" in res.script

        # Execute compiled python script
        exec_res = PythonExecutor.execute_script(res.script_path)
        assert exec_res.success, f"Execution failed: {exec_res.stderr}"
        assert os.path.exists(output_jsonl)

        with open(output_jsonl, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 1
        assert lines[0]["instruction"] == "write a python function."
