import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.compiler.validator import PipelineValidator
from app.compiler.generator import VariableManager, ImportManager, CodeBuilder, PythonGenerator
from app.compiler.ir import PipelineIR, IROperation, IRCall
from app.compiler.compiler import PipelineCompiler, CompilerConfig
from app.compiler.runtime import PythonExecutor


def test_validator_empty_pipeline():
    res = PipelineValidator.validate({"nodes": [], "edges": []})
    assert not res.valid
    assert len(res.errors()) == 1


def test_validator_cycle_detection():
    pipeline = {
        "nodes": [{"id": "n1"}, {"id": "n2"}],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n1"}
        ]
    }
    res = PipelineValidator.validate(pipeline)
    assert not res.valid
    assert any("Cycle detected" in err.message for err in res.errors())


def test_variable_manager():
    vm = VariableManager(base_name="dataset")
    v0 = vm.generate_var(node_id="node_1")
    v1 = vm.generate_var(node_id="node_2")
    v2 = vm.generate_var(node_id="node_3")

    assert v0.name == "dataset"
    assert v1.name == "dataset_1"
    assert v2.name == "dataset_2"
    assert vm.get_var_for_node("node_2") == "dataset_1"


def test_import_manager():
    im = ImportManager()
    im.add_import("polars", alias="pl")
    im.add_import("flowweaver.text", name="normalize")
    im.add_import("flowweaver.text", name="regex_replace")

    statements = im.to_code_lines()
    assert "import polars as pl" in statements
    assert "from flowweaver.text import normalize, regex_replace" in statements


def test_code_builder():
    cb = CodeBuilder()
    cb.line("def main():")
    cb.indent()
    cb.line("print('Hello FlowWeaver')")
    cb.dedent()
    code = cb.to_code()
    assert "def main():\n    print('Hello FlowWeaver')\n" in code


def test_compiler_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = {
            "id": "test_pipeline",
            "nodes": [
                {
                    "id": "import_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "import_dataset",
                        "title": "Import Raw Dataset",
                        "params": {"path": "data/sample.json"}
                    }
                },
                {
                    "id": "normalize_1",
                    "type": "pipelineNode",
                    "data": {
                        "typeId": "unicode_normalize",
                        "title": "Normalize Text",
                        "params": {"column": "text"}
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "import_1", "target": "normalize_1"}
            ]
        }

        config = CompilerConfig(output_dir=tmpdir, script_name="pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        assert res.script_path == os.path.join(tmpdir, "pipeline.py")
        assert os.path.exists(res.script_path)

        with open(res.script_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "def main():" in code
        assert "import_dataset" in code
        assert "unicode_normalize" in code
        assert "dataset =" in code
        assert "dataset_1 =" in code


def test_executor_runs_generated_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "pipeline.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("def main():\n    print('FLOWWEAVER_EXECUTION_SUCCESS')\n\nif __name__ == '__main__':\n    main()\n")

        exec_res = PythonExecutor.execute_script(script_path)
        assert exec_res.success
        assert exec_res.exit_code == 0
        assert "FLOWWEAVER_EXECUTION_SUCCESS" in exec_res.stdout

