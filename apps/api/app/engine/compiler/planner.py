import uuid
from typing import List, Dict, Any
from app.engine.compiler.models import Task, ExecutionPlan

def generate_plan(tasks: List[Task], pipeline_data: Dict[str, Any]) -> ExecutionPlan:
    """Organize logical Tasks into execution stages (layers of concurrency)."""
    stages: List[List[Task]] = []
    
    # Copy task list to mutate
    remaining_tasks = {t.id: t for t in tasks}
    completed_task_ids = set()
    
    while remaining_tasks:
        # Find all tasks where dependencies are fully satisfied
        current_layer = []
        for task_id, task in list(remaining_tasks.items()):
            deps_satisfied = all(dep in completed_task_ids for dep in task.dependencies)
            if deps_satisfied:
                current_layer.append(task)
                
        if not current_layer:
            # Graph has unsortable cycles (should have been captured by validator.py)
            raise ValueError("Execution planner encountered cycle loop.")
            
        stages.append(current_layer)
        for task in current_layer:
            completed_task_ids.add(task.id)
            del remaining_tasks[task.id]
            
    return ExecutionPlan(
        id=f"plan_{uuid.uuid4().hex[:8]}",
        pipelineId=pipeline_data.get("id", "pipeline_unknown"),
        stages=stages,
        variables=pipeline_data.get("variables", {})
    )
