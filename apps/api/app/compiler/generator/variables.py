from typing import Dict, Set, Optional
from app.compiler.ir.variable import IRVariable



class VariableManager:
    """Manages Python variable allocation ensuring non-colliding, readable variable names."""

    def __init__(self, base_name: str = "dataset"):
        self.base_name = base_name
        self.used_names: Set[str] = set()
        self.node_var_map: Dict[str, str] = {}
        self.counter = 0

    def generate_var(self, node_id: Optional[str] = None, prefix: Optional[str] = None) -> IRVariable:
        base = prefix or self.base_name
        if self.counter == 0:
            var_name = base
        else:
            var_name = f"{base}_{self.counter}"

        self.counter += 1
        while var_name in self.used_names:
            var_name = f"{base}_{self.counter}"
            self.counter += 1

        self.used_names.add(var_name)
        if node_id:
            self.node_var_map[node_id] = var_name

        return IRVariable(name=var_name)

    def get_var_for_node(self, node_id: str) -> Optional[str]:
        return self.node_var_map.get(node_id)
