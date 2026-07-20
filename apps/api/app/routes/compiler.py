from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.compiler.compiler import PipelineCompiler
from app.compiler.context import CompilerConfig

router = APIRouter(prefix="/api/compiler", tags=["compiler"])


@router.post("/compile")
def compile_pipeline(payload: Dict[str, Any] = Body(...)):
    """Compile a visual pipeline DAG dictionary into a standalone executable Python script."""
    pipeline_data = payload.get("pipeline") or payload

    config = CompilerConfig(script_name="pipeline.py")
    result = PipelineCompiler.compile(pipeline_data, config)

    if not result.success:
        return {
            "success": False,
            "script": "",
            "script_path": None,
            "errors": result.errors,
            "warnings": result.warnings,
            "validation": result.validation.issues if result.validation else []
        }

    return {
        "success": True,
        "script": result.script,
        "script_path": result.script_path,
        "warnings": result.warnings,
        "errors": [],
        "statistics": result.statistics,
        "execution_time_ms": result.execution_time_ms
    }
