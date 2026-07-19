from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Port(BaseModel):
    id: str
    label: str
    type: str  # tabular, text, image, audio, any
    required: Optional[bool] = False

class Parameter(BaseModel):
    key: str
    label: str
    type: str  # text, number, select, boolean, slider, textarea
    default: Optional[Any] = None
    placeholder: Optional[str] = ""
    options: Optional[List[Dict[str, str]]] = None  # for select: [{"label": "Comma", "value": ","}]
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None

class NodeDefinition(BaseModel):
    id: str
    label: str
    category: str  # Loaders, Filters, Transform, Dedup, NLP, Export
    description: str
    icon: str  # string name of the Lucide icon, e.g. "FileSpreadsheet"
    color: str  # hex color code or custom color
    inputs: List[Port] = []
    outputs: List[Port] = []
    paramsSchema: List[Parameter] = Field(..., alias="params_schema")

    class Config:
        populate_by_name = True
        from_attributes = True

class NodeRegistry:
    def __init__(self):
        self._nodes: Dict[str, NodeDefinition] = {}

    def register(self, node: NodeDefinition):
        self._nodes[node.id] = node

    def get(self, node_id: str) -> Optional[NodeDefinition]:
        return self._nodes.get(node_id)

    def list_all(self) -> List[NodeDefinition]:
        return list(self._nodes.values())

    def validate_config(self, node_id: str, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        node = self.get(node_id)
        if not node:
            return False, [f"Node type '{node_id}' not found in registry."]
        
        errors = []
        # Validate parameters against schema
        for param in node.paramsSchema:
            val = config.get(param.key)
            if val is None:
                continue  # Optional parameter or has default
                
            # Type validation (basic)
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

# Colors matching CAT_COLOR in frontend
COLOR_LOADERS = "#4f86c6"
COLOR_FILTERS = "#c67a4f"
COLOR_TRANSFORM = "#7a4fc6"
COLOR_DEDUP = "#4fc6a0"
COLOR_NLP = "#c64f86"
COLOR_EXPORT = "#c6b74f"

# ─── Loaders ───────────────────────────────────────────────────
registry.register(NodeDefinition(
    id="load_csv", label="Load CSV", category="Loaders",
    description="Read a CSV file from a URL or path",
    icon="FileSpreadsheet", color=COLOR_LOADERS,
    inputs=[], outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="path", label="File path", type="text", default="data/users.csv"),
        Parameter(key="delimiter", label="Delimiter", type="select", default=",", options=[
            {"label": "Comma", "value": ","}, {"label": "Tab", "value": "\t"}, {"label": "Semicolon", "value": ";"}
        ]),
        Parameter(key="header", label="Has header row", type="boolean", default=True),
    ]
))

registry.register(NodeDefinition(
    id="load_json", label="Load JSON", category="Loaders",
    description="Parse a JSON array of records",
    icon="FileText", color=COLOR_LOADERS,
    inputs=[], outputs=[Port(id="out", label="records", type="tabular")],
    params_schema=[
        Parameter(key="path", label="File path", type="text", default="data/records.json"),
        Parameter(key="root", label="Root key", type="text", default="data", placeholder="data"),
    ]
))

registry.register(NodeDefinition(
    id="http_fetch", label="HTTP Fetch", category="Loaders",
    description="Fetch data from a REST endpoint",
    icon="Globe", color=COLOR_LOADERS,
    inputs=[], outputs=[Port(id="out", label="response", type="any")],
    params_schema=[
        Parameter(key="url", label="URL", type="text", default="https://api.example.com/v1/items"),
        Parameter(key="method", label="Method", type="select", default="GET", options=[
            {"label": "GET", "value": "GET"}, {"label": "POST", "value": "POST"}
        ]),
        Parameter(key="timeout", label="Timeout (ms)", type="number", default=5000, min=100, max=60000),
    ]
))

registry.register(NodeDefinition(
    id="load_sql", label="SQL Query", category="Loaders",
    description="Run a SELECT against a database",
    icon="Database", color=COLOR_LOADERS,
    inputs=[], outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="query", label="Query", type="text", default="SELECT * FROM users LIMIT 100"),
        Parameter(key="limit", label="Limit", type="number", default=100, min=1, max=10000),
    ]
))

registry.register(NodeDefinition(
    id="load_s3", label="S3 Bucket", category="Loaders",
    description="List and read objects from S3",
    icon="Cloud", color=COLOR_LOADERS,
    inputs=[], outputs=[Port(id="out", label="objects", type="any")],
    params_schema=[
        Parameter(key="bucket", label="Bucket", type="text", default="my-data-bucket"),
        Parameter(key="prefix", label="Prefix", type="text", default="raw/2024/"),
    ]
))

registry.register(NodeDefinition(
    id="load_images", label="Load Images", category="Loaders",
    description="Read a directory of images",
    icon="ImageIcon", color=COLOR_LOADERS,
    inputs=[], outputs=[Port(id="out", label="images", type="image")],
    params_schema=[
        Parameter(key="path", label="Directory", type="text", default="assets/photos"),
        Parameter(key="recursive", label="Recursive", type="boolean", default=False),
    ]
))

# ─── Filters ───────────────────────────────────────────────────
registry.register(NodeDefinition(
    id="filter_rows", label="Filter Rows", category="Filters",
    description="Keep rows matching a condition",
    icon="Filter", color=COLOR_FILTERS,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="column", label="Column", type="text", default="age"),
        Parameter(key="op", label="Operator", type="select", default=">", options=[
            {"label": ">", "value": ">"}, {"label": "<", "value": "<"}, {"label": "=", "value": "="}, {"label": "!=", "value": "!="}
        ]),
        Parameter(key="value", label="Value", type="text", default="25"),
    ]
))

registry.register(NodeDefinition(
    id="search_text", label="Search Text", category="Filters",
    description="Regex/substring filter on a text column",
    icon="Search", color=COLOR_FILTERS,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="matches", type="tabular")],
    params_schema=[
        Parameter(key="column", label="Column", type="text", default="email"),
        Parameter(key="pattern", label="Pattern", type="text", default="@acme\\.com$"),
        Parameter(key="regex", label="Regex", type="boolean", default=True),
    ]
))

registry.register(NodeDefinition(
    id="sample_rows", label="Sample", category="Filters",
    description="Randomly sample N rows",
    icon="Shuffle", color=COLOR_FILTERS,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="n", label="Sample size", type="slider", default=100, min=1, max=1000),
        Parameter(key="seed", label="Seed", type="number", default=42, min=0, max=999999),
    ]
))

# ─── Transform ─────────────────────────────────────────────────
registry.register(NodeDefinition(
    id="select_columns", label="Select Columns", category="Transform",
    description="Project a subset of columns",
    icon="Columns3", color=COLOR_TRANSFORM,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="columns", label="Columns (comma sep)", type="text", default="id,name,email"),
    ]
))

registry.register(NodeDefinition(
    id="sort_rows", label="Sort", category="Transform",
    description="Sort by a column",
    icon="ArrowUpDown", color=COLOR_TRANSFORM,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="column", label="Column", type="text", default="age"),
        Parameter(key="order", label="Order", type="select", default="asc", options=[
            {"label": "Ascending", "value": "asc"}, {"label": "Descending", "value": "desc"}
        ]),
    ]
))

registry.register(NodeDefinition(
    id="join_rows", label="Join", category="Transform",
    description="Join two tables on a key",
    icon="GitMerge", color=COLOR_TRANSFORM,
    inputs=[
        Port(id="left", label="left", type="tabular", required=True),
        Port(id="right", label="right", type="tabular", required=True),
    ],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="on", label="Join key", type="text", default="id"),
        Parameter(key="how", label="How", type="select", default="inner", options=[
            {"label": "Inner", "value": "inner"}, {"label": "Left", "value": "left"}, {"label": "Outer", "value": "outer"}
        ]),
    ]
))

registry.register(NodeDefinition(
    id="split_col", label="Split Column", category="Transform",
    description="Split a column by a delimiter",
    icon="Scissors", color=COLOR_TRANSFORM,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="column", label="Column", type="text", default="name"),
        Parameter(key="delim", label="Delimiter", type="text", default=" "),
    ]
))

registry.register(NodeDefinition(
    id="map_expr", label="Map Expression", category="Transform",
    description="Compute a new column from an expression",
    icon="Wand2", color=COLOR_TRANSFORM,
    inputs=[Port(id="in", label="rows", type="any", required=True)],
    outputs=[Port(id="out", label="rows", type="any")],
    params_schema=[
        Parameter(key="target", label="New column", type="text", default="full_name"),
        Parameter(key="expr", label="Expression", type="text", default="first + ' ' + last"),
    ]
))

# ─── Dedup ─────────────────────────────────────────────────────
registry.register(NodeDefinition(
    id="dedup_exact", label="Dedup Exact", category="Dedup",
    description="Remove exact duplicate rows",
    icon="Copy", color=COLOR_DEDUP,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="keys", label="Keys (comma sep)", type="text", default="email"),
    ]
))

registry.register(NodeDefinition(
    id="dedup_fuzzy", label="Dedup Fuzzy", category="Dedup",
    description="Fuzzy-match near duplicates",
    icon="Fingerprint", color=COLOR_DEDUP,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[Port(id="out", label="rows", type="tabular")],
    params_schema=[
        Parameter(key="column", label="Column", type="text", default="name"),
        Parameter(key="threshold", label="Similarity threshold", type="slider", default=0.85, min=0.5, max=1.0, step=0.01),
    ]
))

registry.register(NodeDefinition(
    id="normalize", label="Normalize", category="Dedup",
    description="Normalize whitespace, case, encoding",
    icon="SlidersHorizontal", color=COLOR_DEDUP,
    inputs=[Port(id="in", label="rows", type="any", required=True)],
    outputs=[Port(id="out", label="rows", type="any")],
    params_schema=[
        Parameter(key="lower", label="Lowercase", type="boolean", default=True),
        Parameter(key="trim", label="Trim whitespace", type="boolean", default=True),
    ]
))

# ─── NLP ───────────────────────────────────────────────────────
registry.register(NodeDefinition(
    id="tokenize", label="Tokenize", category="NLP",
    description="Split text into tokens",
    icon="Type", color=COLOR_NLP,
    inputs=[Port(id="in", label="text", type="text", required=True)],
    outputs=[Port(id="out", label="tokens", type="any")],
    params_schema=[
        Parameter(key="model", label="Tokenizer", type="select", default="bert", options=[
            {"label": "BERT", "value": "bert"}, {"label": "GPT-BPE", "value": "gpt"}, {"label": "Whitespace", "value": "ws"}
        ]),
    ]
))

registry.register(NodeDefinition(
    id="detect_lang", label="Detect Language", category="NLP",
    description="Identify text language",
    icon="Languages", color=COLOR_NLP,
    inputs=[Port(id="in", label="text", type="text", required=True)],
    outputs=[Port(id="out", label="text+lang", type="text")],
    params_schema=[
        Parameter(key="threshold", label="Confidence", type="slider", default=0.9, min=0.0, max=1.0, step=0.01),
    ]
))

registry.register(NodeDefinition(
    id="sentiment", label="Sentiment", category="NLP",
    description="Classify text sentiment",
    icon="Sparkles", color=COLOR_NLP,
    inputs=[Port(id="in", label="text", type="text", required=True)],
    outputs=[Port(id="out", label="labeled", type="text")],
    params_schema=[
        Parameter(key="model", label="Model", type="select", default="distilbert", options=[
            {"label": "DistilBERT", "value": "distilbert"}, {"label": "VADER", "value": "vader"}
        ]),
    ]
))

registry.register(NodeDefinition(
    id="embed_text", label="Embeddings", category="NLP",
    description="Content vector embeddings",
    icon="Hash", color=COLOR_NLP,
    inputs=[Port(id="in", label="text", type="text", required=True)],
    outputs=[Port(id="out", label="vectors", type="any")],
    params_schema=[
        Parameter(key="model", label="Model", type="select", default="mini-lm", options=[
            {"label": "MiniLM (384)", "value": "mini-lm"}, {"label": "BGE (768)", "value": "bge"}
        ]),
        Parameter(key="batch", label="Batch size", type="number", default=32, min=1, max=512),
    ]
))

registry.register(NodeDefinition(
    id="summarize", label="Summarize", category="NLP",
    description="Abstractive summarization",
    icon="MessageSquare", color=COLOR_NLP,
    inputs=[Port(id="in", label="text", type="text", required=True)],
    outputs=[Port(id="out", label="summaries", type="text")],
    params_schema=[
        Parameter(key="maxLen", label="Max length", type="slider", default=120, min=30, max=400),
    ]
))

# ─── Export ────────────────────────────────────────────────────
registry.register(NodeDefinition(
    id="write_csv", label="Write CSV", category="Export",
    description="Write rows to CSV file",
    icon="Save", color=COLOR_EXPORT,
    inputs=[Port(id="in", label="rows", type="tabular", required=True)],
    outputs=[],
    params_schema=[
        Parameter(key="path", label="Output path", type="text", default="out/results.csv"),
        Parameter(key="compress", label="Gzip", type="boolean", default=False),
    ]
))

registry.register(NodeDefinition(
    id="write_json", label="Write JSON", category="Export",
    description="Serialize records to JSON",
    icon="Download", color=COLOR_EXPORT,
    inputs=[Port(id="in", label="rows", type="any", required=True)],
    outputs=[],
    params_schema=[
        Parameter(key="path", label="Output path", type="text", default="out/results.json"),
        Parameter(key="pretty", label="Pretty print", type="boolean", default=True),
    ]
))

registry.register(NodeDefinition(
    id="webhook", label="Send Webhook", category="Export",
    description="POST rows to an endpoint",
    icon="Send", color=COLOR_EXPORT,
    inputs=[Port(id="in", label="rows", type="any", required=True)],
    outputs=[],
    params_schema=[
        Parameter(key="url", label="Webhook URL", type="text", default="https://hooks.example.com/pipeline"),
        Parameter(key="batch", label="Batch size", type="number", default=100, min=1, max=1000),
    ]
))

registry.register(NodeDefinition(
    id="upload_s3", label="Upload S3", category="Export",
    description="Upload files to S3",
    icon="Upload", color=COLOR_EXPORT,
    inputs=[Port(id="in", label="data", type="any", required=True)],
    outputs=[],
    params_schema=[
        Parameter(key="bucket", label="Bucket", type="text", default="processed-data"),
        Parameter(key="key", label="Key", type="text", default="runs/{date}/output.parquet"),
    ]
))
