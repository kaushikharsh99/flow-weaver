from typing import List, Dict, Any, Optional
from flowweaver.sdk import Node, Port, Parameter
from app.engine.nodes.loaders import LoadCSVNode, LoadJSONNode
from app.engine.nodes.filters import FilterRowsNode
from app.engine.nodes.exports import WriteCSVNode
from app.engine.nodes.fallback import FallbackNode

class NodeRegistry:
    def __init__(self):
        self._nodes: Dict[str, Node] = {}

    def register(self, node: Node):
        self._nodes[node.id] = node

    def get(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def list_all(self) -> List[Node]:
        return list(self._nodes.values())

    def validate_config(self, node_id: str, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        node = self.get(node_id)
        if not node:
            return False, [f"Node type '{node_id}' not found in registry."]
        
        errors = []
        # Validate parameters against schema
        for param in node.params_schema:
            val = config.get(param.key)
            if val is None:
                continue
                
            if param.type == "number" or param.type == "slider":
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

# Create global registry instance
registry = NodeRegistry()

# Register core implementations
registry.register(LoadCSVNode())
registry.register(LoadJSONNode())
registry.register(FilterRowsNode())
registry.register(WriteCSVNode())

# Seed fallback nodes to complete the 24 built-in list
fallback_node_ids = [
    ("http_fetch", "HTTP Fetch", "Loaders", "Fetch data from a REST endpoint", "Globe", "#4f86c6", [], [Port(id="out", label="response", type="any")]),
    ("load_sql", "SQL Query", "Loaders", "Run a SELECT against a database", "Database", "#4f86c6", [], [Port(id="out", label="rows", type="tabular")]),
    ("load_s3", "S3 Bucket", "Loaders", "List and read objects from S3", "Cloud", "#4f86c6", [], [Port(id="out", label="objects", type="any")]),
    ("load_images", "Load Images", "Loaders", "Read a directory of images", "ImageIcon", "#4f86c6", [], [Port(id="out", label="images", type="image")]),
    ("search_text", "Search Text", "Filters", "Regex/substring filter on a text column", "Search", "#c67a4f", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="matches", type="tabular")]),
    ("sample_rows", "Sample", "Filters", "Randomly sample N rows", "Shuffle", "#c67a4f", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("select_columns", "Select Columns", "Transform", "Project a subset of columns", "Columns3", "#7a4fc6", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("sort_rows", "Sort", "Transform", "Sort by a column", "ArrowUpDown", "#7a4fc6", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("join_rows", "Join", "Transform", "Join two tables on a key", "GitMerge", "#7a4fc6", [Port(id="left", label="left", type="tabular", required=True), Port(id="right", label="right", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("split_col", "Split Column", "Transform", "Split a column by a delimiter", "Scissors", "#7a4fc6", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("map_expr", "Map Expression", "Transform", "Compute a new column from an expression", "Wand2", "#7a4fc6", [Port(id="in", label="rows", type="any", required=True)], [Port(id="out", label="rows", type="any")]),
    ("dedup_exact", "Dedup Exact", "Dedup", "Remove exact duplicate rows", "Copy", "#4fc6a0", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("dedup_fuzzy", "Dedup Fuzzy", "Dedup", "Fuzzy-match near duplicates", "Fingerprint", "#4fc6a0", [Port(id="in", label="rows", type="tabular", required=True)], [Port(id="out", label="rows", type="tabular")]),
    ("normalize", "Normalize", "Dedup", "Normalize whitespace, case, encoding", "SlidersHorizontal", "#4fc6a0", [Port(id="in", label="rows", type="any", required=True)], [Port(id="out", label="rows", type="any")]),
    ("tokenize", "Tokenize", "NLP", "Split text into tokens", "Type", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="tokens", type="any")]),
    ("detect_lang", "Detect Language", "NLP", "Identify text language", "Languages", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="text+lang", type="text")]),
    ("sentiment", "Sentiment", "NLP", "Classify text sentiment", "Sparkles", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="labeled", type="text")]),
    ("embed_text", "Embeddings", "NLP", "Content vector embeddings", "Hash", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="vectors", type="any")]),
    ("summarize", "Summarize", "NLP", "Abstractive summarization", "MessageSquare", "#c64f86", [Port(id="in", label="text", type="text", required=True)], [Port(id="out", label="summaries", type="text")]),
    ("write_json", "Write JSON", "Export", "Serialize records to JSON", "Download", "#c6b74f", [Port(id="in", label="rows", type="any", required=True)], []),
    ("webhook", "Send Webhook", "Export", "POST rows to an endpoint", "Send", "#c6b74f", [Port(id="in", label="rows", type="any", required=True)], []),
    ("upload_s3", "Upload S3", "Export", "Upload files to S3", "Upload", "#c6b74f", [Port(id="in", label="data", type="any", required=True)], []),
]

for node_id, label, cat, desc, icon, color, inputs, outputs in fallback_node_ids:
    fallback_node = FallbackNode(node_id)
    fallback_node.label = label
    fallback_node.category = cat
    fallback_node.description = desc
    fallback_node.icon = icon
    fallback_node.color = color
    fallback_node.inputs = inputs
    fallback_node.outputs = outputs
    fallback_node.params_schema = []
    registry.register(fallback_node)
