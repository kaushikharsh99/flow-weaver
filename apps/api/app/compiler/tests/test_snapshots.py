import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.compiler.compiler import PipelineCompiler, CompilerConfig

SNAPSHOT_FINE_TUNING = '''"""
FlowWeaver Generated Preprocessing Script
Pipeline: tpl_llm_finetuning
Generated: Auto-compiled visual DAG script

DO NOT EDIT DIRECTLY — Changes will be overwritten upon compiler re-generation.
"""

from app.engine.nodes.core_logic import import_dataset, lowercase, unicode_normalize, remove_empty, write_jsonl


def main():
    # Load Raw Dataset (load_1)
    dataset = import_dataset(path='data/sample.csv', delimiter=',')

    # Lowercase Instructions (lowercase_1)
    dataset_1 = lowercase(dataset, column='name')

    # Normalize Unicode NFC (normalize_1)
    dataset_2 = unicode_normalize(dataset_1, column='name', form='NFC')

    # Filter Empty Rows (remove_empty_1)
    dataset_3 = remove_empty(dataset_2, columns='name,score')

    # Export Fine-tuning JSONL (export_1)
    dataset_4 = write_jsonl(dataset_3, path='out/finetuning_prep.jsonl')


if __name__ == '__main__':
    main()
'''




def test_llm_finetuning_pipeline_snapshot():
    pipeline = {
        "id": "tpl_llm_finetuning",
        "nodes": [
            {
                "id": "load_1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "import_dataset",
                    "title": "Load Raw Dataset",
                    "params": {"path": "data/sample.csv", "delimiter": ","}
                }
            },
            {
                "id": "lowercase_1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "lowercase",
                    "title": "Lowercase Instructions",
                    "params": {"column": "name"}
                }
            },
            {
                "id": "normalize_1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "unicode_normalize",
                    "title": "Normalize Unicode NFC",
                    "params": {"column": "name", "form": "NFC"}
                }
            },
            {
                "id": "remove_empty_1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "remove_empty",
                    "title": "Filter Empty Rows",
                    "params": {"columns": "name,score"}
                }
            },
            {
                "id": "export_1",
                "type": "pipelineNode",
                "data": {
                    "typeId": "write_jsonl",
                    "title": "Export Fine-tuning JSONL",
                    "params": {"path": "out/finetuning_prep.jsonl"}
                }
            }
        ],
        "edges": [
            {"id": "e1", "source": "load_1", "target": "lowercase_1"},
            {"id": "e2", "source": "lowercase_1", "target": "normalize_1"},
            {"id": "e3", "source": "normalize_1", "target": "remove_empty_1"},
            {"id": "e4", "source": "remove_empty_1", "target": "export_1"}
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config = CompilerConfig(output_dir=tmpdir, script_name="pipeline.py")
        res = PipelineCompiler.compile(pipeline, config)

        assert res.success
        assert "def main():" in res.script
        assert "from flowweaver.std.io import import_dataset" in res.script
        assert "from flowweaver.std.text import lowercase" in res.script

        # Verify M2: argparse, logging, progress
        assert "import argparse" in res.script
        assert "import logging" in res.script
        assert "def parse_args():" in res.script
        assert '--input' in res.script
        assert '--output' in res.script
        assert 'logger.info("Starting pipeline:' in res.script

        # Verify section-separated formatting with step counts
        assert "# Step 1/5: Import Dataset" in res.script
        assert "# Step 2/5: Normalize Text to Lowercase" in res.script
        assert "# Step 3/5: Apply Unicode Normalization" in res.script
        assert "# " + "-" * 56 in res.script

        # Verify semantic variable names
        assert "raw_dataset = import_dataset" in res.script
        assert "normalized_dataset = lowercase" in res.script

        # Verify argparse path substitution
        assert "path=args.input" in res.script
        assert "path=args.output" in res.script

