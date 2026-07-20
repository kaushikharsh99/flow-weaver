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


from app.compiler.ir import IRCall, IRConstant


class DatasetRef:
    """Fluent API wrapper for compiling dataset operations."""

    def __init__(self, ctx: "CompilerContext", var_name: Optional[str] = None):
        self.ctx = ctx
        self.var_name = var_name or ctx.input_var

    def call(self, func_path: str, **kwargs: Any) -> IRCall:
        args = [self.var_name] if self.var_name else []
        return self.ctx.call(func_path, *args, **kwargs)

    def lowercase(self, column: str) -> IRCall:
        return self.call("flowweaver.std.text.lowercase", column=column)

    def uppercase(self, column: str) -> IRCall:
        return self.call("flowweaver.std.text.uppercase", column=column)

    def unicode_normalize(self, column: str, form: str = "NFC") -> IRCall:
        return self.call("flowweaver.std.text.unicode_normalize", column=column, form=form)

    def strip_whitespace(self, column: str) -> IRCall:
        return self.call("flowweaver.std.text.strip_whitespace", column=column)

    def regex_replace(self, column: str, pattern: str, replacement: str) -> IRCall:
        return self.call("flowweaver.std.text.regex_replace", column=column, pattern=pattern, replacement=replacement)

    def select_columns(self, columns: List[str]) -> IRCall:
        return self.call("flowweaver.std.tabular.select_columns", columns=columns)

    def rename_columns(self, rename_map: Dict[str, str]) -> IRCall:
        return self.call("flowweaver.std.tabular.rename_columns", rename_map=rename_map)

    def filter_rows(self, column: str, operator: str = "==", value: Any = "") -> IRCall:
        return self.call("flowweaver.std.tabular.filter_rows", column=column, operator=operator, value=value)

    def sort_rows(self, by: str, ascending: bool = True) -> IRCall:
        return self.call("flowweaver.std.tabular.sort_rows", by=by, ascending=ascending)

    def sample_rows(self, n: int = 100, seed: int = 42) -> IRCall:
        return self.call("flowweaver.std.tabular.sample_rows", n=n, seed=seed)

    def shuffle(self, seed: int = 42) -> IRCall:
        return self.call("flowweaver.std.tabular.shuffle", seed=seed)

    def drop_columns(self, columns: List[str]) -> IRCall:
        return self.call("flowweaver.std.tabular.drop_columns", columns=columns)

    def split_dataset(self, ratio: float = 0.8, seed: int = 42) -> IRCall:
        return self.call("flowweaver.std.tabular.split_dataset", ratio=ratio, seed=seed)

    def concatenate(self, other_var: str) -> IRCall:
        return self.call("flowweaver.std.tabular.concatenate", other=other_var)

    def dedup_exact(self, columns: Optional[List[str]] = None) -> IRCall:
        return self.call("flowweaver.std.dedup.dedup_exact", columns=columns)

    def simhash_deduplicate(self, column: str, threshold: int = 3) -> IRCall:
        return self.call("flowweaver.std.dedup.simhash_deduplicate", column=column, threshold=threshold)

    def export_csv(self, path: str) -> IRCall:
        return self.call("flowweaver.std.io.export_csv", path=path)

    def export_jsonl(self, path: str) -> IRCall:
        return self.call("flowweaver.std.io.export_jsonl", path=path)

    def export_parquet(self, path: str) -> IRCall:
        return self.call("flowweaver.std.io.export_parquet", path=path)


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

    def dataset(self, var_name: Optional[str] = None) -> DatasetRef:
        """Returns a fluent DatasetRef helper for authoring node compilation."""
        return DatasetRef(self, var_name=var_name)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_error(self, msg: str):
        self.errors.append(msg)

    def require_import(self, module: str, alias: Optional[str] = None, name: Optional[str] = None):
        self.imports.add_import(module, alias=alias, name=name)

    def call(self, func_path: str, *args: Any, **kwargs: Any) -> IRCall:
        """Helper to create an IRCall while automatically registering the required import."""
        from app.compiler.ir import IRVariable as _IRVariable

        parts = func_path.rsplit(".", 1)
        if len(parts) == 2:
            module, name = parts[0], parts[1]
            self.require_import(module, name=name)
            func_name = name
        else:
            func_name = func_path

        # Wrap string args that are variable references as IRVariable
        wrapped_args = []
        for a in args:
            if isinstance(a, str) and self._is_variable_name(a):
                wrapped_args.append(_IRVariable(name=a))
            else:
                wrapped_args.append(a)

        return IRCall(function=func_name, args=wrapped_args, kwargs=kwargs)

    def _is_variable_name(self, name: str) -> bool:
        """Check if a string looks like a Python variable name (vs a user-provided value)."""
        if not name or (not name[0].isalpha() and name[0] != '_'):
            return False
        # Known variable patterns from the compiler
        if name == "dataset" or name.startswith("dataset_") or name.endswith("_dataset"):
            return True
        # Check if it matches any allocated variable name
        if hasattr(self, 'variables') and name in self.variables.used_names:
            return True
        # Semantic variable names with numeric suffixes (e.g. normalized_dataset_1)
        import re
        if re.match(r'^[a-z_]+_dataset(?:_\d+)?$', name):
            return True
        return False

    def constant(self, val: Any) -> IRConstant:
        return IRConstant(value=val)

    def comment(self, text: str):
        self.metadata.setdefault("comments", []).append(text)


