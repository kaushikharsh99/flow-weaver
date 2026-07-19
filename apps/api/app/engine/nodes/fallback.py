import time
import random
from typing import Dict, Any
from app.engine.base import BaseNode, ExecutionContext

class FallbackNode(BaseNode):
    def __init__(self, node_type_id: str):
        self.node_type_id = node_type_id

    def execute(self, ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Executing fallback simulated handler for node type '{self.node_type_id}'")
        
        # Simulate delay
        delay = 0.3 + random.random() * 0.6
        time.sleep(delay)
        
        # Provide some dummy outputs based on node type
        outputs = {}
        if self.node_type_id == "sentiment":
            outputs["out"] = {"sentiment": "positive", "confidence": 0.94}
        elif self.node_type_id == "tokenize":
            outputs["out"] = ["simulated", "tokenized", "output"]
        else:
            outputs["out"] = ctx.inputs.get("in", "Simulated Output")
            
        return outputs
