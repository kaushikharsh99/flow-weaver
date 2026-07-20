import os
import time
import json
from typing import Dict, Any, Optional, List, Set

from app.compiler.validator import PipelineValidator, ValidationResult
from app.compiler.context import CompilerContext, CompilerConfig
from app.compiler.result import CompilerResult
from app.compiler.ir import PipelineIR, IROperation, IRCall, IRConstant
from app.compiler.generator import PythonGenerator
from app.engine.registry import registry


NODE_MODULE_MAP = {
    "import_dataset": ("flowweaver.std.io", "import_dataset"),
    "load_file": ("flowweaver.std.io", "import_dataset"),
    "load_csv": ("flowweaver.std.io", "import_dataset"),
    "load_json": ("flowweaver.std.io", "import_dataset"),
    "load_jsonl": ("flowweaver.std.io", "import_dataset"),
    "load_parquet": ("flowweaver.std.io", "import_dataset"),

    "unicode_normalize": ("flowweaver.std.text", "unicode_normalize"),
    "lowercase": ("flowweaver.std.text", "lowercase"),
    "uppercase": ("flowweaver.std.text", "uppercase"),
    "strip_whitespace": ("flowweaver.std.text", "strip_whitespace"),
    "regex_replace": ("flowweaver.std.text", "regex_replace"),

    "select_columns": ("flowweaver.std.tabular", "select_columns"),
    "rename_columns": ("flowweaver.std.tabular", "rename_columns"),
    "filter_rows": ("flowweaver.std.tabular", "filter_rows"),
    "sort_rows": ("flowweaver.std.tabular", "sort_rows"),
    "drop_columns": ("flowweaver.std.tabular", "drop_columns"),
    "sample_rows": ("flowweaver.std.tabular", "sample_rows"),
    "shuffle": ("flowweaver.std.tabular", "shuffle"),
    "split_dataset": ("flowweaver.std.tabular", "split_dataset"),
    "concatenate": ("flowweaver.std.tabular", "concatenate"),
    "statistics": ("flowweaver.std.tabular", "statistics"),

    "dedup_exact": ("flowweaver.std.dedup", "dedup_exact"),
    "simhash_deduplicate": ("flowweaver.std.dedup", "simhash_deduplicate"),

    "write_csv": ("flowweaver.std.io", "export_csv"),
    "write_json": ("flowweaver.std.io", "export_json"),
    "write_jsonl": ("flowweaver.std.io", "export_jsonl"),
    "write_parquet": ("flowweaver.std.io", "export_parquet"),
    "export_csv": ("flowweaver.std.io", "export_csv"),
    "export_json": ("flowweaver.std.io", "export_json"),
    "export_jsonl": ("flowweaver.std.io", "export_jsonl"),
    "export_parquet": ("flowweaver.std.io", "export_parquet"),
}




class PipelineCompiler:
    """FlowWeaver Visual Pipeline Compiler.
    
    Transforms visual DAG pipelines into standalone, runnable, production-ready Python scripts.
    """

    @classmethod
    def compile(cls, pipeline_dict: Dict[str, Any], config: Optional[CompilerConfig] = None) -> CompilerResult:
        start_time = time.time()
        config = config or CompilerConfig()
        ctx = CompilerContext(config)

        # Step 1: Validate Pipeline
        validation: ValidationResult = PipelineValidator.validate(pipeline_dict)
        if not validation.valid:
            err_msgs = [f"[{i.node_id or 'global'}] {i.message}" for i in validation.errors()]
            warn_msgs = [f"[{i.node_id or 'global'}] {i.message}" for i in validation.warnings()]
            return CompilerResult(
                success=False,
                script="",
                script_path=None,
                validation=validation,
                errors=err_msgs,
                warnings=warn_msgs,
                execution_time_ms=(time.time() - start_time) * 1000.0
            )

        # Step 2: Build Topological Execution Order
        nodes = pipeline_dict.get("nodes", [])
        edges = pipeline_dict.get("edges", [])
        node_map = {n.get("id"): n for n in nodes if n.get("id")}

        adj: Dict[str, List[str]] = {n_id: [] for n_id in node_map}
        in_degree: Dict[str, int] = {n_id: 0 for n_id in node_map}
        edge_map: Dict[str, List[Dict[str, Any]]] = {n_id: [] for n_id in node_map}

        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in adj and tgt in in_degree:
                adj[src].append(tgt)
                in_degree[tgt] += 1
                edge_map[tgt].append(edge)

        queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
        topo_order: List[str] = []

        while queue:
            curr = queue.pop(0)
            topo_order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Step 3: Build Pipeline IR
        pipeline_name = pipeline_dict.get("id", "pipeline")
        ir = PipelineIR(name=pipeline_name)

        # Track node output variable mapping
        node_var_map: Dict[str, str] = {}

        for n_id in topo_order:
            node_data = node_map[n_id]
            inner_data = node_data.get("data", {})
            type_id = inner_data.get("typeId") or inner_data.get("type", n_id)
            params = inner_data.get("params", {})
            title = inner_data.get("title", type_id)

            # Determine input variable references
            incoming_edges = edge_map.get(n_id, [])
            input_var = None
            if incoming_edges:
                src_node_id = incoming_edges[0].get("source")
                input_var = node_var_map.get(src_node_id)

            # Allocate output variable with semantic naming
            out_var = ctx.variables.generate_var(node_id=n_id, type_id=type_id)
            node_var_map[n_id] = out_var.name


            ctx.current_node_id = n_id
            ctx.input_var = input_var
            ctx.output_var = out_var.name
            ctx.current_params = params


            # Check registry for compile implementation or fallback generator
            node_instance = registry.get(type_id)
            if node_instance and hasattr(node_instance, "compile") and callable(node_instance.compile):
                custom_ir = node_instance.compile(ctx)
                if custom_ir:
                    op = IROperation(
                        id=n_id,
                        node_type=type_id,
                        target_variable=out_var.name,
                        expression=custom_ir,
                        comment=f"{title} ({n_id})"
                    )
                    ir.operations.append(op)
                    continue


            # Default Operation IR Construction
            if type_id in NODE_MODULE_MAP:
                module_name, func_name = NODE_MODULE_MAP[type_id]
            else:
                module_name = f"flowweaver.{type_id.split('_')[0]}"
                func_name = type_id

            ctx.require_import(module_name, name=func_name)


            call_args = []
            if input_var:
                call_args.append(input_var)

            call_kwargs = dict(params)

            op = IROperation(
                id=n_id,
                node_type=type_id,
                target_variable=out_var.name,
                expression=IRCall(function=func_name, args=call_args, kwargs=call_kwargs),
                comment=f"{title} ({n_id})"
            )
            ir.operations.append(op)

        ir.imports = ctx.imports.get_imports()
        ir.variables = list(ctx.variables.used_names)

        # Step 4: Python Code Generation
        generator = PythonGenerator()
        script_code = generator.generate(ir)

        # Step 5: Write pipeline.py
        os.makedirs(config.output_dir, exist_ok=True)
        script_path = os.path.join(config.output_dir, config.script_name)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_code)

        # Create sample directories
        os.makedirs(os.path.join(config.output_dir, "sample_input"), exist_ok=True)
        os.makedirs(os.path.join(config.output_dir, "sample_output"), exist_ok=True)

        # Write config.yaml
        input_path, output_path = generator._detect_io_paths(ir)
        config_yaml_content = f"""# FlowWeaver Pipeline Configuration
pipeline_name: "{pipeline_name}"
input_path: "{input_path or ''}"
output_path: "{output_path or ''}"
"""
        with open(os.path.join(config.output_dir, "config.yaml"), "w", encoding="utf-8") as f:
            f.write(config_yaml_content)

        # Write LICENSE
        license_content = """MIT License

Copyright (c) 2026 FlowWeaver

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        with open(os.path.join(config.output_dir, "LICENSE"), "w", encoding="utf-8") as f:
            f.write(license_content)

        # Step 6: Build Complete Pipeline Artifact Package
        duration_ms = (time.time() - start_time) * 1000.0

        # 6a. Write pipeline.json (Visual DAG Source)
        with open(os.path.join(config.output_dir, "pipeline.json"), "w", encoding="utf-8") as f:
            json.dump(pipeline_dict, f, indent=2)

        # 6b. Write pipeline.lock (Dependency Lock) and requirements.txt
        detected_packages = ir.metadata.get("requirements", [])
        package_version_map = {
            "polars": "polars>=0.20.0",
            "pyarrow": "pyarrow>=14.0.0",
            "xxhash": "xxhash>=3.0.0",
        }
        
        lock_deps = {}
        requirements_lines = []
        for pkg in detected_packages:
            mapped_ver = package_version_map.get(pkg, pkg)
            lock_deps[pkg] = mapped_ver.split(">=")[-1] if ">=" in mapped_ver else ">=0.0.1"
            requirements_lines.append(mapped_ver)
            
        lock_data = {
            "flowweaver_version": "0.1.0",
            "python_version": config.target_python_version,
            "dependencies": lock_deps,
            "nodes": [op.node_type for op in ir.operations]
        }
        
        with open(os.path.join(config.output_dir, "pipeline.lock"), "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)

        # Write requirements.txt
        requirements_path = os.path.join(config.output_dir, "requirements.txt")
        with open(requirements_path, "w", encoding="utf-8") as f:
            if requirements_lines:
                f.write("\n".join(requirements_lines) + "\n")
            else:
                f.write("# No external third-party dependencies required.\n")

        # 6c. Write metadata.json (Compilation Report & Statistics)
        metadata_data = {
            "pipeline_name": pipeline_name,
            "compiled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_time_ms": round(duration_ms, 2),
            "generated_loc": len(script_code.splitlines()),
            "operations_count": len(ir.operations),
            "imports_count": len(ir.imports),
            "variables_count": len(ir.variables),
            "requirements": requirements_lines,
            "operations": [{"id": op.id, "type": op.node_type, "variable": op.target_variable} for op in ir.operations]
        }
        with open(os.path.join(config.output_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # 6d. Write README.md (Documentation & Usage)
        readme_content = f"""# ⚡ FlowWeaver Compiled Pipeline: `{pipeline_name}`

> Automatically generated production Python preprocessing build package by FlowWeaver Compiler.

## 🚀 Execution Guide

Run the self-contained pipeline directly with Python:

```bash
python {config.script_name}
```

### CLI Arguments & Parameters

```bash
python {config.script_name} --help
```

- `--input`: Override input dataset path
- `--output`: Override output destination path
- `--limit`: Limit row count for rapid testing
- `--verbose`: Enable detailed log output

## 📦 Package Contents
- `{config.script_name}`: Standalone senior-engineer quality Python preprocessing script.
- `pipeline.json`: Visual DAG source definition.
- `pipeline.lock`: Reproducible dependency lock file.
- `metadata.json`: Compilation statistics & node execution trace.
- `logs/`: Execution runtime log directory.
"""
        with open(os.path.join(config.output_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)

        os.makedirs(os.path.join(config.output_dir, "logs"), exist_ok=True)

        return CompilerResult(
            success=True,
            script=script_code,
            script_path=script_path,
            validation=validation,
            warnings=ctx.warnings,
            errors=[],
            statistics=metadata_data,
            execution_time_ms=duration_ms
        )

