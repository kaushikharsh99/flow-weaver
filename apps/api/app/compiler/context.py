from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.compiler.generator.variables import VariableManager
from app.compiler.generator.imports import ImportManager


@dataclass
class CompilerConfig:
    output_dir: str = "out"
    script_name: str = "pipeline.py"
    target_python_version: str = "3.11"
    format_output: bool = True
    variables: Dict[str, Any] = field(default_factory=dict)


from app.compiler.ir import IRCall


class CompilerContext:
    """Stores state, variable allocations, imports, warnings, and errors during compilation."""

    def __init__(self, config: Optional[CompilerConfig] = None):
        self.config = config or CompilerConfig()
        self.variables = VariableManager()
        self.imports = ImportManager()
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.current_node_id: Optional[str] = None
        self.input_var: Optional[str] = None
        self.output_var: Optional[str] = None
        self.current_params: Dict[str, Any] = {}

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_error(self, msg: str):
        self.errors.append(msg)

    def require_import(self, module: str, alias: Optional[str] = None, name: Optional[str] = None):
        self.imports.add_import(module, alias=alias, name=name)

    def call(self, func_path: str, *args: Any, **kwargs: Any) -> IRCall:
        """Helper to create an IRCall while automatically registering the required import.
        
        Example: ctx.call("flowweaver.std.text.lowercase", dataset_var, column="instruction")
        """
        parts = func_path.rsplit(".", 1)
        if len(parts) == 2:
            module, name = parts[0], parts[1]
            self.require_import(module, name=name)
            func_name = name
        else:
            func_name = func_path

        return IRCall(function=func_name, args=list(args), kwargs=kwargs)

