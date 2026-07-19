from typing import List, Dict, Any
from app.engine.compiler.models import Task

def optimize_tasks(tasks: List[Task], pipeline_data: Dict[str, Any]) -> List[Task]:
    """Apply DAG compiler optimizations (e.g. checkpoint reuse, redundant node pruning)."""
    # Feature 1: Checkpoint Caching Check
    # For now, we mock caching evaluation by checking if nodes are configured for cache
    # or have run successfully in cache before (in production, we compare input checksums).
    for task in tasks:
        # Check if node has a custom cache settings config
        params = task.parameters
        if params.get("use_cache") is True or params.get("__cached__") is True:
            task.is_cached = True
            
    return tasks
