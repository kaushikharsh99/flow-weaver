from typing import Dict, List, Set, Optional
from app.compiler.ir.imports import IRImport


class ImportManager:
    """Manages Python module imports without duplicates or conflicts."""

    def __init__(self):
        # module -> IRImport
        self._imports: Dict[str, IRImport] = {}

    def add_import(self, module: str, alias: Optional[str] = None, name: Optional[str] = None):
        key = (module, alias)
        if key in self._imports:
            imp = self._imports[key]
            if name and imp.names is not None:
                if name not in imp.names:
                    imp.names.append(name)
        else:
            names_list = [name] if name else None
            self._imports[key] = IRImport(module=module, alias=alias, names=names_list)

    def get_imports(self) -> List[IRImport]:
        return list(self._imports.values())

    def to_code_lines(self) -> List[str]:
        lines = []
        for imp in sorted(self._imports.values(), key=lambda i: (i.module, i.alias or "")):
            lines.append(imp.to_statement())
        return lines
