import os
import time
from typing import Dict, Any, Optional, List, Set
from app.compiler.validator import PipelineValidator, ValidationResult
from app.compiler.context import CompilerContext, CompilerConfig
from app.compiler.result import CompilerResult
from app.compiler.ir import PipelineIR, IROperation, IRCall, IRConstant
from app.compiler.generator import PythonGenerator
from app.engine.registry import registry


CORE_LOGIC_MODULE = "app.engine.nodes.core_logic"

NODE_MODULE_MAP = {
    "import_dataset": (CORE_LOGIC_MODULE, "import_dataset"),
    "load_file": (CORE_LOGIC_MODULE, "import_dataset"),
    "load_csv": (CORE_LOGIC_MODULE, "import_dataset"),
    "load_json": (CORE_LOGIC_MODULE, "import_dataset"),
    "load_jsonl": (CORE_LOGIC_MODULE, "import_dataset"),
    "load_parquet": (CORE_LOGIC_MODULE, "import_dataset"),
    "unicode_normalize": (CORE_LOGIC_MODULE, "unicode_normalize"),
    "lowercase": (CORE_LOGIC_MODULE, "lowercase"),
    "strip_html": (CORE_LOGIC_MODULE, "strip_html"),
    "regex_replace": (CORE_LOGIC_MODULE, "regex_replace"),
    "chunk_text": (CORE_LOGIC_MODULE, "chunk_text"),
    "remove_empty": (CORE_LOGIC_MODULE, "remove_empty"),
    "filter_rows": (CORE_LOGIC_MODULE, "filter_rows"),
    "length_filter": (CORE_LOGIC_MODULE, "length_filter"),
    "language_filter": (CORE_LOGIC_MODULE, "language_filter"),
    "dedup_exact": (CORE_LOGIC_MODULE, "dedup_exact"),
    "write_csv": (CORE_LOGIC_MODULE, "write_csv"),
    "write_jsonl": (CORE_LOGIC_MODULE, "write_jsonl"),
    "write_parquet": (CORE_LOGIC_MODULE, "write_parquet"),
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

            # Allocate output variable
            out_var = ctx.variables.generate_var(node_id=n_id, prefix="dataset")
            node_var_map[n_id] = out_var.name

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

        duration_ms = (time.time() - start_time) * 1000.0

        return CompilerResult(
            success=True,
            script=script_code,
            script_path=script_path,
            validation=validation,
            warnings=ctx.warnings,
            errors=[],
            statistics={
                "operations_count": len(ir.operations),
                "imports_count": len(ir.imports),
                "variables_count": len(ir.variables)
            },
            execution_time_ms=duration_ms
        )
