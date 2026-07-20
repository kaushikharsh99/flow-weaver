import os
import ast
import sys
from typing import Dict, Set, List, Tuple, Optional

# Standard library module list (fallback for Python < 3.10)
STDLIB_MODULES = getattr(sys, 'stdlib_module_names', {
    "abc", "argparse", "ast", "asyncio", "base64", "collections", "copy", "csv",
    "dataclasses", "datetime", "enum", "functools", "hashlib", "importlib",
    "inspect", "io", "json", "logging", "math", "os", "pathlib", "random", "re",
    "shutil", "sys", "time", "typing", "unicodedata", "urllib", "warnings"
})

CORE_KEEP_METHODS = {
    "__init__", "__repr__", "__iter__", "__len__", "__getitem__", "__enter__", "__exit__",
    "metadata", "schema", "history", "columns", "row_count", "to_list", "with_history", "iter_chunks"
}


class SymbolReferenceVisitor(ast.NodeVisitor):
    """Collects all identifier names and attribute names referenced in an AST."""
    def __init__(self):
        self.referenced_names: Set[str] = set()
        self.referenced_attrs: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        self.referenced_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.referenced_attrs.add(node.attr)
        self.generic_visit(node)


class PipelineLinker:
    """FlowWeaver Linker & Dependency Analyzer with Tree-Shaking.
    
    Parses flowweaver.std source code using AST, traces reachable functions,
    constants, and classes, prunes unreferenced methods & dead code, deduplicates
    and groups imports, and bundles a minimal, zero-dependency standalone script block.
    """

    CLASS_ORDER = [
        "ColumnSchema",
        "DatasetSchema",
        "DatasetMetadata",
        "OperationRecord",
        "Dataset",
        "TabularDataset",
        "PolarsDataset",
        "ArrowDataset",
        "StreamingDataset"
    ]

    UTIL_ORDER = [
        "validate_dataset",
        "validate_column_exists",
        "validate_columns_exist",
        "validate_not_empty",
        "ProgressTracker"
    ]

    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        d = current_dir
        self.std_dir = ""
        while d and d != os.path.dirname(d):
            candidate = os.path.join(d, "packages", "flowweaver_sdk", "flowweaver", "std")
            if os.path.exists(candidate):
                self.std_dir = candidate
                break
            d = os.path.dirname(d)
        
        self.definitions: Dict[str, Tuple[str, str, ast.AST, List[ast.AST]]] = {}
        self.name_to_file: Dict[str, str] = {}
        self._build_std_name_map()

    def _build_std_name_map(self):
        """Scans standard library source files and maps top-level symbols to definitions and imports."""
        if not os.path.exists(self.std_dir):
            return

        for root, _, files in os.walk(self.std_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.std_dir)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=filepath)
                        
                        file_imports = [
                            n for n in tree.body
                            if isinstance(n, (ast.Import, ast.ImportFrom))
                        ]

                        for node in tree.body:
                            names_in_node = []
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                names_in_node.append(node.name)
                            elif isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        names_in_node.append(target.id)

                            for name in names_in_node:
                                self.definitions[name] = (rel_path, filepath, node, file_imports)
                                self.name_to_file[name] = rel_path
                    except Exception:
                        pass

    def link(self, required_operations: List[str], extra_imports: Optional[List[str]] = None) -> Tuple[str, List[str]]:
        """Link and bundle only reachable operations, helpers, and classes.
        
        Returns:
            inlined_code: Standalone Python source code string.
            requirements: List of third-party package dependencies detected during linking.
        """
        resolved_nodes: List[Tuple[str, ast.AST]] = []
        resolved_names: Set[str] = set()
        file_imports_collected: List[ast.AST] = []

        queue = list(required_operations)

        # Step 1: Reachability analysis using BFS
        while queue:
            name = queue.pop(0)
            if name in resolved_names or name not in self.definitions:
                continue

            resolved_names.add(name)
            rel_path, filepath, target_node, file_imports = self.definitions[name]
            resolved_nodes.append((name, target_node))
            file_imports_collected.extend(file_imports)

            # Trace references inside target_node
            visitor = SymbolReferenceVisitor()
            visitor.visit(target_node)

            for dep in visitor.referenced_names:
                if dep in self.definitions and dep not in resolved_names:
                    queue.append(dep)

            # Trace base classes if target_node is a ClassDef
            if isinstance(target_node, ast.ClassDef):
                for base in target_node.bases:
                    if isinstance(base, ast.Name) and base.id in self.definitions and base.id not in resolved_names:
                        queue.append(base.id)

        # Step 2: Collect all referenced attributes & names across all resolved nodes
        global_visitor = SymbolReferenceVisitor()
        for _, node in resolved_nodes:
            global_visitor.visit(node)

        referenced_attrs = global_visitor.referenced_attrs

        # Step 3: Class Method Pruning (Dead code elimination inside classes)
        pruned_resolved_nodes: List[Tuple[str, ast.AST]] = []
        for name, node in resolved_nodes:
            if isinstance(node, ast.ClassDef):
                new_body = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_name = item.name
                        if (
                            m_name in CORE_KEEP_METHODS
                            or m_name.startswith("__")
                            or m_name in referenced_attrs
                            or any(isinstance(dec, ast.Name) and dec.id in ("classmethod", "staticmethod") for dec in item.decorator_list)
                        ):
                            new_body.append(item)
                    else:
                        new_body.append(item)
                
                cloned_class = ast.ClassDef(
                    name=node.name,
                    bases=node.bases,
                    keywords=node.keywords,
                    body=new_body,
                    decorator_list=node.decorator_list
                )
                pruned_resolved_nodes.append((name, cloned_class))
            else:
                pruned_resolved_nodes.append((name, node))

        # Re-scan referenced names after method pruning
        final_visitor = SymbolReferenceVisitor()
        for _, node in pruned_resolved_nodes:
            final_visitor.visit(node)
        final_names = final_visitor.referenced_names

        # Step 4: Import Optimization & Deduplication
        simple_imports: Set[Tuple[str, Optional[str]]] = set()
        from_imports: Dict[str, Set[Tuple[str, Optional[str]]]] = {}
        third_party_packages: Set[str] = set()

        if extra_imports:
            for extra_imp in extra_imports:
                simple_imports.add((extra_imp, None))

        for imp in file_imports_collected:
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    mod_name = alias.name
                    if mod_name.startswith("flowweaver"):
                        continue
                    as_name = alias.asname
                    check_symbol = as_name or mod_name.split(".")[0]
                    if check_symbol in final_names or mod_name.split(".")[0] in final_names:
                        simple_imports.add((mod_name, as_name))
                        top_pkg = mod_name.split(".")[0]
                        if top_pkg not in STDLIB_MODULES:
                            third_party_packages.add(top_pkg)

            elif isinstance(imp, ast.ImportFrom):
                mod_name = imp.module or ""
                if mod_name.startswith("flowweaver") or not mod_name:
                    continue
                top_pkg = mod_name.split(".")[0]

                for alias in imp.names:
                    sym_name = alias.name
                    as_name = alias.asname
                    check_symbol = as_name or sym_name
                    if check_symbol in final_names or check_symbol == "*":
                        names_set = from_imports.setdefault(mod_name, set())
                        names_set.add((sym_name, as_name))
                        if top_pkg not in STDLIB_MODULES:
                            third_party_packages.add(top_pkg)

        # Format import lines (PEP 8 grouped)
        stdlib_simple = []
        stdlib_from = {}
        third_simple = []
        third_from = {}

        for mod, asname in simple_imports:
            top_pkg = mod.split(".")[0]
            if top_pkg in STDLIB_MODULES:
                stdlib_simple.append((mod, asname))
            else:
                third_simple.append((mod, asname))

        for mod, pairs in from_imports.items():
            top_pkg = mod.split(".")[0]
            if top_pkg in STDLIB_MODULES:
                stdlib_from[mod] = pairs
            else:
                third_from[mod] = pairs

        import_blocks = []

        # Stdlib imports
        stdlib_lines = []
        for mod, asname in sorted(stdlib_simple):
            line = f"import {mod} as {asname}" if asname else f"import {mod}"
            stdlib_lines.append(line)
        for mod in sorted(stdlib_from.keys()):
            items = []
            for name, asname in sorted(list(stdlib_from[mod])):
                items.append(f"{name} as {asname}" if asname else name)
            stdlib_lines.append(f"from {mod} import {', '.join(items)}")

        if stdlib_lines:
            import_blocks.append("\n".join(stdlib_lines))

        # Third-party imports
        third_lines = []
        for mod, asname in sorted(third_simple):
            line = f"import {mod} as {asname}" if asname else f"import {mod}"
            third_lines.append(line)
        for mod in sorted(third_from.keys()):
            items = []
            for name, asname in sorted(list(third_from[mod])):
                items.append(f"{name} as {asname}" if asname else name)
            third_lines.append(f"from {mod} import {', '.join(items)}")

        if third_lines:
            import_blocks.append("\n".join(third_lines))

        # Step 5: Organize inlined code blocks logically
        constants_blocks: List[str] = []
        classes_blocks: List[Tuple[str, str]] = []
        utils_blocks: List[Tuple[str, str]] = []
        ops_blocks: List[str] = []

        for name, node in pruned_resolved_nodes:
            code_str = ast.unparse(node)
            if isinstance(node, ast.Assign):
                constants_blocks.append(code_str)
            elif isinstance(node, ast.ClassDef):
                classes_blocks.append((name, code_str))
            elif name in self.UTIL_ORDER:
                utils_blocks.append((name, code_str))
            else:
                ops_blocks.append(code_str)

        def get_class_index(item: Tuple[str, str]) -> int:
            try:
                return self.CLASS_ORDER.index(item[0])
            except ValueError:
                return len(self.CLASS_ORDER)
        classes_blocks.sort(key=get_class_index)

        def get_util_index(item: Tuple[str, str]) -> int:
            try:
                return self.UTIL_ORDER.index(item[0])
            except ValueError:
                return len(self.UTIL_ORDER)
        utils_blocks.sort(key=get_util_index)

        inlined_parts = []
        if import_blocks:
            inlined_parts.append("\n\n".join(import_blocks))
            inlined_parts.append("")

        if constants_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Global Constants")
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("\n\n".join(constants_blocks))
            inlined_parts.append("")

        if classes_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Core Dataset Engineering Classes")
            inlined_parts.append("# " + "=" * 54)
            class_code = "\n\n".join([code for _, code in classes_blocks])
            inlined_parts.append(class_code)
            inlined_parts.append("")

        if utils_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Helper Validation & Instrumentation Utilities")
            inlined_parts.append("# " + "=" * 54)
            util_code = "\n\n".join([code for _, code in utils_blocks])
            inlined_parts.append(util_code)
            inlined_parts.append("")

        if ops_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Pipeline Standard Operations")
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("\n\n".join(ops_blocks))
            inlined_parts.append("")

        return "\n".join(inlined_parts), sorted(list(third_party_packages))
