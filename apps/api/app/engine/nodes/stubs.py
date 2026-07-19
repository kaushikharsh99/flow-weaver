"""Built-in stub nodes for node types that don't have full implementations yet.

Each node is self-describing using the declarative @node decorator.
They are auto-discovered by the registry — no manual registration needed.
"""
import time
import random
from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext, TabularDataset, Port


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

@node(name="HTTP Fetch", category="Loaders", icon="Globe",
      description="Fetch data from a REST endpoint")
class HttpFetchNode(Node):
    id = "http_fetch"
    output = Output.any(label="response")
    url = Param.text(label="URL", placeholder="https://api.example.com/data")
    method = Param.select(label="Method", default="GET", options=[
        {"label": "GET", "value": "GET"}, {"label": "POST", "value": "POST"}
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Fetching data from URL (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"response": "stub"}], columns=["response"])}


@node(name="SQL Query", category="Loaders", icon="Database",
      description="Run a SELECT against a database")
class LoadSQLNode(Node):
    id = "load_sql"
    output = Output.tabular(label="rows")
    query = Param.textarea(label="SQL Query", default="SELECT * FROM users LIMIT 10", rows=4)
    connection = Param.text(label="Connection String", placeholder="sqlite:///data.db")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Executing SQL query (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"id": 1, "name": "stub"}], columns=["id", "name"])}


@node(name="S3 Bucket", category="Loaders", icon="Cloud",
      description="List and read objects from S3")
class LoadS3Node(Node):
    id = "load_s3"
    output = Output.any(label="objects")
    bucket = Param.text(label="Bucket Name", placeholder="my-bucket")
    prefix = Param.text(label="Key Prefix", placeholder="data/")
    access_key = Param.secret(label="Access Key")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Reading S3 bucket (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"key": "stub.csv"}], columns=["key"])}


@node(name="Load Images", category="Loaders", icon="ImageIcon",
      description="Read a directory of images")
class LoadImagesNode(Node):
    id = "load_images"
    output = Output.image(label="images")
    directory = Param.file(label="Image Directory", placeholder="/path/to/images")
    pattern = Param.regex(label="File Pattern", default=".*\\.(png|jpg|jpeg)")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Loading images from directory (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"path": "image.png"}], columns=["path"])}


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

@node(name="Search Text", category="Filters", icon="Search",
      description="Regex/substring filter on a text column")
class SearchTextNode(Node):
    id = "search_text"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="matches")
    column = Param.column(label="Search Column", default="text")
    pattern = Param.regex(label="Search Pattern", default=".*error.*")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Searching text (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Sample", category="Filters", icon="Shuffle",
      description="Randomly sample N rows")
class SampleRowsNode(Node):
    id = "sample_rows"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    count = Param.number(label="Sample Size", default=100, min=1, max=100000)
    seed = Param.number(label="Random Seed", default=42)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Sampling rows (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

@node(name="Select Columns", category="Transform", icon="Columns3",
      description="Project a subset of columns")
class SelectColumnsNode(Node):
    id = "select_columns"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    columns = Param.text(label="Columns", placeholder="col1, col2, col3")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Selecting columns (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Sort", category="Transform", icon="ArrowUpDown",
      description="Sort by a column")
class SortRowsNode(Node):
    id = "sort_rows"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    column = Param.column(label="Sort Column")
    ascending = Param.boolean(label="Ascending", default=True)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Sorting rows (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Join", category="Transform", icon="GitMerge",
      description="Join two tables on a key")
class JoinRowsNode(Node):
    id = "join_rows"
    inputs = [
        Port(id="left", label="left", type="tabular", required=True),
        Port(id="right", label="right", type="tabular", required=True),
    ]
    output = Output.tabular(label="rows")
    join_key = Param.column(label="Join Key", default="id")
    join_type = Param.select(label="Join Type", default="inner", options=[
        {"label": "Inner", "value": "inner"}, {"label": "Left", "value": "left"},
        {"label": "Right", "value": "right"}, {"label": "Outer", "value": "outer"},
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Joining tables (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("left", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Split Column", category="Transform", icon="Scissors",
      description="Split a column by a delimiter")
class SplitColNode(Node):
    id = "split_col"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    column = Param.column(label="Column to Split")
    delimiter = Param.text(label="Delimiter", default=",")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Splitting column (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Map Expression", category="Transform", icon="Wand2",
      description="Compute a new column from an expression")
class MapExprNode(Node):
    id = "map_expr"
    data = Input.any(label="rows")
    output = Output.any(label="rows")
    expression = Param.expression(label="Expression", placeholder="col_a + col_b")
    output_column = Param.text(label="Output Column", default="result")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Mapping expression (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("data", TabularDataset([], columns=[]))
        return {"output": out}


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------

@node(name="Dedup Exact", category="Dedup", icon="Copy",
      description="Remove exact duplicate rows")
class DedupExactNode(Node):
    id = "dedup_exact"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    columns = Param.text(label="Dedup Columns", placeholder="col1, col2 (empty = all)")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Deduplicating rows (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Dedup Fuzzy", category="Dedup", icon="Fingerprint",
      description="Fuzzy-match near duplicates")
class DedupFuzzyNode(Node):
    id = "dedup_fuzzy"
    rows = Input.tabular(label="rows")
    output = Output.tabular(label="rows")
    column = Param.column(label="Match Column")
    threshold = Param.slider(label="Similarity Threshold", default=0.85, min=0.0, max=1.0, step=0.01)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Fuzzy deduplicating (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("rows", TabularDataset([], columns=[]))
        return {"output": out}


@node(name="Normalize", category="Dedup", icon="SlidersHorizontal",
      description="Normalize whitespace, case, encoding")
class NormalizeNode(Node):
    id = "normalize"
    data = Input.any(label="rows")
    output = Output.any(label="rows")
    lowercase = Param.boolean(label="Lowercase", default=True)
    strip_whitespace = Param.boolean(label="Strip Whitespace", default=True)
    unicode_normalize = Param.boolean(label="Unicode NFC", default=True)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Normalizing text (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        out = inputs.get("data", TabularDataset([], columns=[]))
        return {"output": out}


# ---------------------------------------------------------------------------
# NLP
# ---------------------------------------------------------------------------

@node(name="Tokenize", category="NLP", icon="Type",
      description="Split text into tokens")
class TokenizeNode(Node):
    id = "tokenize"
    text = Input.text(label="text")
    output = Output.any(label="tokens")
    tokenizer = Param.select(label="Tokenizer", default="whitespace", options=[
        {"label": "Whitespace", "value": "whitespace"},
        {"label": "Word", "value": "word"},
        {"label": "Sentence", "value": "sentence"},
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Tokenizing text (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"tokens": "stub"}], columns=["tokens"])}


@node(name="Detect Language", category="NLP", icon="Languages",
      description="Identify text language")
class DetectLangNode(Node):
    id = "detect_lang"
    text = Input.text(label="text")
    output = Output.text(label="text+lang")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Detecting language (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"text": "stub", "lang": "en"}], columns=["text", "lang"])}


@node(name="Sentiment", category="NLP", icon="Sparkles",
      description="Classify text sentiment")
class SentimentNode(Node):
    id = "sentiment"
    text = Input.text(label="text")
    output = Output.text(label="labeled")
    model = Param.select(label="Model", default="vader", options=[
        {"label": "VADER", "value": "vader"}, {"label": "TextBlob", "value": "textblob"}
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Classifying sentiment (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"text": "stub", "sentiment": 0.8}], columns=["text", "sentiment"])}


@node(name="Embeddings", category="NLP", icon="Hash",
      description="Generate content vector embeddings")
class EmbedTextNode(Node):
    id = "embed_text"
    text = Input.text(label="text")
    output = Output.any(label="vectors")
    model = Param.select(label="Model", default="all-MiniLM-L6-v2", options=[
        {"label": "MiniLM-L6", "value": "all-MiniLM-L6-v2"},
        {"label": "E5 Large", "value": "e5-large"},
    ])
    batch_size = Param.number(label="Batch Size", default=32, min=1, max=512)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Generating embeddings (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"vector": "[0.1, 0.2, ...]"}], columns=["vector"])}


@node(name="Summarize", category="NLP", icon="MessageSquare",
      description="Abstractive text summarization")
class SummarizeNode(Node):
    id = "summarize"
    text = Input.text(label="text")
    output = Output.text(label="summaries")
    max_length = Param.slider(label="Max Length", default=150, min=10, max=1000, step=10)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Summarizing text (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {"output": TabularDataset([{"summary": "stub summary"}], columns=["summary"])}


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@node(name="Write JSON", category="Export", icon="Download",
      description="Serialize records to JSON")
class WriteJSONNode(Node):
    id = "write_json"
    data = Input.any(label="rows")
    path = Param.file(label="Output Path", default="out/results.json")
    pretty = Param.boolean(label="Pretty Print", default=True)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Writing JSON (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {}


@node(name="Send Webhook", category="Export", icon="Send",
      description="POST rows to an endpoint")
class WebhookNode(Node):
    id = "webhook"
    data = Input.any(label="rows")
    url = Param.text(label="Webhook URL", placeholder="https://hooks.example.com/data")
    headers = Param.json(label="Headers", default='{"Content-Type": "application/json"}')

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Sending webhook (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {}


@node(name="Upload S3", category="Export", icon="Upload",
      description="Upload files to S3")
class UploadS3Node(Node):
    id = "upload_s3"
    data = Input.any(label="data")
    bucket = Param.text(label="Bucket Name", placeholder="my-bucket")
    key_prefix = Param.text(label="Key Prefix", default="output/")
    access_key = Param.secret(label="Access Key")
    secret_key = Param.secret(label="Secret Key")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        ctx.log(f"Uploading to S3 (stub)")
        time.sleep(0.2 + random.random() * 0.3)
        return {}
