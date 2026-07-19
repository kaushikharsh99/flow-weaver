#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def run_db_engine_test(python_exec: str, api_dir: str):
    """Test SQL query schema generation & topological compiler stages directly."""
    test_code = """
import sys
sys.path.insert(0, ".")
from app.db import SessionLocal
from app import models
from app.engine.registry import registry
from app.engine.compiler.validator import validate_pipeline
from app.engine.compiler.builder import build_tasks
from app.engine.compiler.optimizer import optimize_tasks
from app.engine.compiler.planner import generate_plan

# 1. Test Registry loading
nodes = registry.list_all()
print(f"✔ Registry loaded successfully. Node types found: {len(nodes)}")
assert len(nodes) >= 24, "Registry missing core nodes!"

# 2. Test Compilation stages
dummy_pipeline = {
    "id": "test_pipe_smoke",
    "nodes": [
        {
            "id": "load_1",
            "type": "pipelineNode",
            "data": {
                "typeId": "load_csv",
                "params": {"path": "data/users.csv", "delimiter": ","}
            }
        },
        {
            "id": "write_1",
            "type": "pipelineNode",
            "data": {
                "typeId": "write_csv",
                "params": {"path": "out/users.csv"}
            }
        }
    ],
    "edges": [
        {
            "id": "edge_1",
            "source": "load_1",
            "target": "write_1",
            "sourceHandle": "out",
            "targetHandle": "in_data"
        }
    ]
}

# Validator check
val_res = validate_pipeline(dummy_pipeline)
print(f"✔ Semantic Validator running: valid={val_res.valid}")

# Builder check
tasks = build_tasks(dummy_pipeline)
print(f"✔ Graph Builder: tasks count={len(tasks)}")

# Optimizer check
optimized_tasks = optimize_tasks(tasks, dummy_pipeline)
print("✔ Graph Optimizer completed.")

# Planner check
plan = generate_plan(optimized_tasks, dummy_pipeline)
print(f"✔ Planner generated plan stages: {len(plan.stages)}")

print("✔ Backend compiler stages smoke test passed!")
"""
    subprocess.check_call([python_exec, "-c", test_code], cwd=api_dir)

def run_typecheck_test(root_dir: str):
    """Test frontend TS compiler check."""
    print("Running frontend type checks...")
    try:
        subprocess.check_call(["npm", "run", "typecheck:web"], cwd=root_dir)
        print("✔ Frontend workspace typecheck completed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Error: Frontend type check failed.")
        sys.exit(1)

def main():
    print("==================================================")
    print("           FlowWeaver Smoke Testing Suite         ")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_dir = os.path.join(root_dir, "apps/api")
    venv_dir = os.path.join(api_dir, "venv")
    
    if platform.system() == "Windows":
        python_exec = os.path.join(venv_dir, "Scripts", "python")
    else:
        python_exec = os.path.join(venv_dir, "bin", "python")
        
    if not os.path.exists(python_exec):
        print("❌ Error: Environment setup missing. Run python scripts/install.py first.")
        sys.exit(1)
        
    try:
        run_db_engine_test(python_exec, api_dir)
        run_typecheck_test(root_dir)
        print("\\n==================================================")
        print("✔ All FlowWeaver smoke tests passed successfully!")
        print("==================================================")
    except Exception as e:
        print(f"❌ Testing suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
