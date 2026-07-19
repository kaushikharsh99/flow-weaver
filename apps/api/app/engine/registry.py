"""
FlowWeaver Node Registry — Auto-Discovery Engine

Boot sequence:
    Scan built-in nodes → Import → Validate → Register
    Scan plugins/ → Load plugin.yaml → Import → Validate → Register
    → Expose via /api/nodes

Zero manual registration. The developer never touches this file.
"""
import os
import sys
import yaml
import importlib
import importlib.util
import inspect
from typing import List, Dict, Any, Optional
from flowweaver.sdk import Node, Port, Parameter


class NodeRegistry:
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._loaded_plugins: List[Dict[str, Any]] = []

    def register(self, node: Node):
        """Register a node instance. Used internally by auto-discovery."""
        self._nodes[node.id] = node

    def get(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def list_all(self) -> List[Node]:
        return list(self._nodes.values())

    def list_plugins(self) -> List[Dict[str, Any]]:
        return self._loaded_plugins

    def validate_config(self, node_id: str, config: Dict[str, Any]) -> tuple:
        """Validate a parameter configuration against the node's schema."""
        node = self.get(node_id)
        if not node:
            return False, [f"Node type '{node_id}' not found in registry."]

        errors = []
        for param in node.params_schema:
            val = config.get(param.key)
            if val is None:
                continue

            if param.type in ("number", "slider"):
                if not isinstance(val, (int, float)):
                    errors.append(f"Parameter '{param.key}' must be a number.")
                else:
                    if param.min is not None and val < param.min:
                        errors.append(f"Parameter '{param.key}' must be >= {param.min}.")
                    if param.max is not None and val > param.max:
                        errors.append(f"Parameter '{param.key}' must be <= {param.max}.")
            elif param.type == "boolean":
                if not isinstance(val, bool):
                    errors.append(f"Parameter '{param.key}' must be a boolean.")
            elif param.type == "select":
                if param.options:
                    valid_values = {opt["value"] for opt in param.options}
                    if str(val) not in valid_values:
                        errors.append(f"Parameter '{param.key}' value '{val}' is not a valid option.")

        return len(errors) == 0, errors

    # ------------------------------------------------------------------
    # Auto-discovery: built-in nodes
    # ------------------------------------------------------------------

    def discover_builtin_nodes(self, nodes_package_dir: str):
        """Scan a Python package directory for Node subclasses and register them all.

        This eliminates manual registration. Just create a .py file with Node subclasses
        in the nodes/ directory and they'll be discovered automatically.
        """
        if not os.path.isdir(nodes_package_dir):
            return

        package_name = "app.engine.nodes"

        for filename in sorted(os.listdir(nodes_package_dir)):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue

            module_name = f"{package_name}.{filename[:-3]}"
            try:
                mod = importlib.import_module(module_name)
                self._register_nodes_from_module(mod, source=f"builtin:{filename}")
            except Exception as e:
                print(f"  ⚠ Failed to import built-in module '{module_name}': {e}")

    def _register_nodes_from_module(self, module, source: str = ""):
        """Find all Node subclasses in a module and register instances."""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Must be a subclass of Node, not Node itself, and not imported from elsewhere
            if (issubclass(obj, Node) and
                    obj is not Node and
                    obj.__module__ == module.__name__ and
                    hasattr(obj, "id") and obj.id):
                try:
                    instance = obj()
                    if instance.id and instance.id not in self._nodes:
                        self.register(instance)
                        print(f"  ✔ Registered node '{instance.label}' [{instance.id}] from {source}")
                except Exception as e:
                    print(f"  ⚠ Failed to instantiate {name}: {e}")

    # ------------------------------------------------------------------
    # Auto-discovery: local plugins
    # ------------------------------------------------------------------

    def load_local_plugins(self, plugins_dir: str):
        """Scan and load local plugins dynamically from plugin.yaml config files."""
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)
            return

        # Add plugins directory to sys.path to allow dynamic imports
        abs_plugins_dir = os.path.abspath(plugins_dir)
        if abs_plugins_dir not in sys.path:
            sys.path.insert(0, abs_plugins_dir)

        print(f"Scanning for plugins in: {plugins_dir}...")
        for entry in sorted(os.listdir(plugins_dir)):
            full_path = os.path.join(plugins_dir, entry)
            if os.path.isdir(full_path):
                yaml_path = os.path.join(full_path, "plugin.yaml")
                if os.path.exists(yaml_path):
                    try:
                        with open(yaml_path, "r") as f:
                            meta = yaml.safe_load(f)

                        plugin_id = meta.get("id")
                        nodes_list = meta.get("nodes", [])

                        # Add plugin directory to path so imports within it resolve correctly
                        abs_full_path = os.path.abspath(full_path)
                        if abs_full_path not in sys.path:
                            sys.path.insert(0, abs_full_path)

                        # Load custom node classes declared in yaml
                        loaded_node_ids = []
                        for node_path in nodes_list:
                            module_name, class_name = node_path.rsplit(".", 1)
                            # Dynamically import module
                            mod = importlib.import_module(module_name)
                            node_class = getattr(mod, class_name)

                            # Instantiate node
                            node_instance = node_class()
                            self.register(node_instance)
                            loaded_node_ids.append(node_instance.id)
                            print(f"  ✔ Loaded plugin node '{node_instance.label}' [{node_instance.id}] from plugin '{plugin_id}'.")

                        self._loaded_plugins.append({
                            "id": plugin_id,
                            "name": meta.get("name", plugin_id),
                            "version": meta.get("version", "0.1.0"),
                            "author": meta.get("author", "Unknown"),
                            "nodes": loaded_node_ids
                        })

                    except Exception as e:
                        print(f"  ⚠ Failed to load plugin '{entry}': {str(e)}")


# Create global registry instance
registry = NodeRegistry()

# Auto-discover all built-in nodes from the nodes/ package
# This replaces ALL manual registry.register() calls
_nodes_dir = os.path.join(os.path.dirname(__file__), "nodes")
print("Discovering built-in nodes...")
registry.discover_builtin_nodes(_nodes_dir)
print(f"Registry loaded: {len(registry.list_all())} node(s) registered.")

# Note: Dynamic plugin loading is triggered separately in main.py startup
