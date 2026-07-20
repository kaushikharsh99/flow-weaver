import os
import ast
from typing import Dict, Set, List, Tuple


class DependencyVisitor(ast.NodeVisitor):
    """AST visitor that collects all referenced names matching standard library definitions."""
    def __init__(self, name_to_file: Dict[str, str]):
        self.dependencies = set()
        self.name_to_file = name_to_file

    def visit_Name(self, node: ast.Name):
        if node.id in self.name_to_file:
            self.dependencies.add(node.id)
        self.generic_visit(node)


class PipelineLinker:
    """FlowWeaver Linker & Dependency Analyzer.
    
    Parses flowweaver.std source code using AST, traces required functions,
    constants, and classes, and bundles them into a standalone, zero-dependency block.
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
        # Resolve the flowweaver_sdk/flowweaver/std directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
        self.std_dir = os.path.join(repo_root, "packages", "flowweaver_sdk", "flowweaver", "std")
        
        # Maps name -> relative filepath in flowweaver/std/
        self.name_to_file = self._build_std_name_map()

    def _build_std_name_map(self) -> Dict[str, str]:
        """Scans all standard library source files dynamically and maps definitions to files."""
        name_to_file = {}
        if not os.path.exists(self.std_dir):
            return name_to_file

        for root, _, files in os.walk(self.std_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.std_dir)
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=filepath)
                        for node in tree.body:
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                name_to_file[node.name] = rel_path
                            elif isinstance(node, ast.ClassDef):
                                name_to_file[node.name] = rel_path
                            elif isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        name_to_file[target.id] = rel_path
                    except Exception:
                        pass
        return name_to_file

    def link(self, required_operations: List[str]) -> Tuple[str, List[str]]:
        """Link and bundle only the required operations, helpers, and classes.
        
        Returns a tuple of:
          - inlined_code: Standalone Python source code string.
          - requirements: List of third-party package dependencies detected during linking.
        """
        resolved_nodes: List[Tuple[str, ast.AST]] = []
        resolved_names: Set[str] = set()
        simple_imports: Set[str] = set()
        from_imports: Dict[str, Set[str]] = {}
        detected_packages: Set[str] = set()

        # Build initial queue from entrypoint operations
        queue = list(required_operations)

        # Tracing dependencies using BFS
        while queue:
            name = queue.pop(0)
            if name in resolved_names:
                continue

            rel_path = self.name_to_file.get(name)
            if not rel_path:
                continue

            resolved_names.add(name)
            filepath = os.path.join(self.std_dir, rel_path)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()
                tree = ast.parse(file_content, filename=filepath)

                # Step 1: Scan top-level imports in this file
                for node in tree.body:
                    if isinstance(node, ast.Import):
                        for name_node in node.names:
                            if not name_node.name.startswith("flowweaver"):
                                simple_imports.add(name_node.name)
                                # Track package name for requirements.txt
                                pkg_base = name_node.name.split(".")[0]
                                if pkg_base not in ("os", "sys", "json", "csv", "re", "math", "time", "hashlib", "unicodedata", "abc", "typing", "dataclasses", "inspect"):
                                    detected_packages.add(pkg_base)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and not node.module.startswith("flowweaver"):
                            names_set = from_imports.setdefault(node.module, set())
                            for alias in node.names:
                                names_set.add(alias.name)
                            # Track package name for requirements.txt
                            pkg_base = node.module.split(".")[0]
                            if pkg_base not in ("os", "sys", "json", "csv", "re", "math", "time", "hashlib", "unicodedata", "abc", "typing", "dataclasses", "inspect"):
                                    detected_packages.add(pkg_base)

                # Step 2: Locate and extract definition node
                target_node = None
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                        target_node = node
                        break
                    elif isinstance(node, ast.ClassDef) and node.name == name:
                        target_node = node
                        break
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == name:
                                target_node = node
                                break
                        if target_node:
                            break

                if target_node:
                    resolved_nodes.append((name, target_node))
                    # Trace names referenced in this definition
                    visitor = DependencyVisitor(self.name_to_file)
                    visitor.visit(target_node)
                    for dep in visitor.dependencies:
                        if dep not in resolved_names:
                            queue.append(dep)

            except Exception:
                pass

        # Organize inlined blocks logically to ensure proper declaration order
        constants_blocks: List[str] = []
        classes_blocks: List[Tuple[str, str]] = []
        utils_blocks: List[Tuple[str, str]] = []
        ops_blocks: List[str] = []

        for name, node in resolved_nodes:
            code_str = ast.unparse(node)
            
            if isinstance(node, ast.Assign):
                constants_blocks.append(code_str)
            elif isinstance(node, ast.ClassDef):
                classes_blocks.append((name, code_str))
            elif name in self.UTIL_ORDER:
                utils_blocks.append((name, code_str))
            else:
                ops_blocks.append(code_str)

        # Sort classes based on class dependency order
        def get_class_index(item: Tuple[str, str]) -> int:
            try:
                return self.CLASS_ORDER.index(item[0])
            except ValueError:
                return len(self.CLASS_ORDER)
        classes_blocks.sort(key=get_class_index)

        # Sort utility functions
        def get_util_index(item: Tuple[str, str]) -> int:
            try:
                return self.UTIL_ORDER.index(item[0])
            except ValueError:
                return len(self.UTIL_ORDER)
        utils_blocks.sort(key=get_util_index)

        # Assemble the inlined code sections
        inlined_parts = []
        
        # Imports collected from standard library
        import_lines = []
        for imp in sorted(list(simple_imports)):
            import_lines.append(f"import {imp}")
        for mod in sorted(from_imports.keys()):
            names = sorted(list(from_imports[mod]))
            import_lines.append(f"from {mod} import {', '.join(names)}")
        if import_lines:
            inlined_parts.append("\n".join(import_lines))
            inlined_parts.append("")

        # Constants
        if constants_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Global Constants")
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("\n\n".join(constants_blocks))
            inlined_parts.append("")

        # Base Classes & Datasets
        if classes_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Core Dataset Engineering Classes")
            inlined_parts.append("# " + "=" * 54)
            class_code = "\n\n".join([code for _, code in classes_blocks])
            inlined_parts.append(class_code)
            inlined_parts.append("")

        # Utilities
        if utils_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Helper Validation & Instrumentation Utilities")
            inlined_parts.append("# " + "=" * 54)
            util_code = "\n\n".join([code for _, code in utils_blocks])
            inlined_parts.append(util_code)
            inlined_parts.append("")

        # Operations
        if ops_blocks:
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("# Pipeline Standard Operations")
            inlined_parts.append("# " + "=" * 54)
            inlined_parts.append("\n\n".join(ops_blocks))
            inlined_parts.append("")

        return "\n".join(inlined_parts), sorted(list(detected_packages))
