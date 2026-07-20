from typing import Dict, Set, Optional
from app.compiler.ir.variable import IRVariable



NODE_SEMANTIC_PREFIX_MAP = {
    "import_dataset": "raw_dataset",
    "load_file": "raw_dataset",
    "load_csv": "raw_dataset",
    "load_json": "raw_dataset",
    "load_jsonl": "raw_dataset",
    "load_parquet": "raw_dataset",

    "lowercase": "normalized_dataset",
    "uppercase": "normalized_dataset",
    "unicode_normalize": "normalized_dataset",
    "strip_whitespace": "cleaned_dataset",
    "regex_replace": "cleaned_dataset",
    "strip_html": "cleaned_dataset",

    "filter_rows": "filtered_dataset",
    "length_filter": "filtered_dataset",
    "remove_empty": "filtered_dataset",

    "dedup_exact": "deduplicated_dataset",
    "simhash_deduplicate": "deduplicated_dataset",

    "select_columns": "transformed_dataset",
    "rename_columns": "transformed_dataset",

    "write_csv": "processed_dataset",
    "write_jsonl": "processed_dataset",
    "write_parquet": "processed_dataset",
    "export_csv": "processed_dataset",
    "export_jsonl": "processed_dataset",
    "export_parquet": "processed_dataset",
}


class VariableManager:
    """Manages Python variable allocation ensuring non-colliding, highly readable semantic variable names."""

    def __init__(self, base_name: str = "dataset"):
        self.base_name = base_name
        self.used_names: Set[str] = set()
        self.node_var_map: Dict[str, str] = {}

    def generate_var(self, node_id: Optional[str] = None, type_id: Optional[str] = None, prefix: Optional[str] = None) -> IRVariable:
        if prefix:
            base = prefix
        elif type_id and type_id in NODE_SEMANTIC_PREFIX_MAP:
            base = NODE_SEMANTIC_PREFIX_MAP[type_id]
        else:
            base = self.base_name

        if base not in self.used_names:
            var_name = base
        else:
            idx = 1
            while f"{base}_{idx}" in self.used_names:
                idx += 1
            var_name = f"{base}_{idx}"

        self.used_names.add(var_name)
        if node_id:
            self.node_var_map[node_id] = var_name

        return IRVariable(name=var_name)

    def get_var_for_node(self, node_id: str) -> Optional[str]:
        return self.node_var_map.get(node_id)

