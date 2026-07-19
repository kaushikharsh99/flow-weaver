import time
import random
from typing import Dict, Any
from flowweaver.sdk import Node, ExecutionContext, TabularDataset

class FallbackNode(Node):
    def __init__(self, node_type_id: str):
        self.node_type_id = node_type_id
        self.id = node_type_id

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Executing fallback handler for dynamic node type '{self.node_type_id}'")
        
        # Simulate delay
        delay = 0.2 + random.random() * 0.4
        time.sleep(delay)
        
        # Provide some dummy outputs
        out_val = inputs.get("in", "Simulated Output")
        
        # Wrap string/list in TabularDataset if appropriate
        if isinstance(out_val, str):
            out_val = TabularDataset([{"text": out_val}], columns=["text"])
        elif isinstance(out_val, list):
            out_val = TabularDataset([{"item": x} for x in out_val], columns=["item"])
            
        return {"out": out_val}
