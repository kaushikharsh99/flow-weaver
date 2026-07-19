from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from app.engine.nodes.core_logic import tokenize_text_column, chunk_text_column, rename_dataset_columns

@node(name="Tokenize Text", category="Transform", icon="Scissors", description="Tokenize text column into word or sentence tokens lists")
class TokenizeNode(Node):
    id = "tokenize"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Tokenized Rows")
    
    column = Param.column(label="Target Column", default="text")
    mode = Param.select(label="Tokenization Mode", default="word", options=[
        {"label": "Word Tokenization", "value": "word"},
        {"label": "Sentence Tokenization", "value": "sentence"}
    ])

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        mode = ctx.parameters.get("mode", "word")
        return {"out": tokenize_text_column(dataset, col, mode)}


@node(name="Text Chunking", category="Transform", icon="Layers", description="Chunk long text columns using a sliding word window for RAG prep")
class ChunkTextNode(Node):
    id = "chunk_text"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Chunked Rows")
    
    column = Param.column(label="Target Column", default="text")
    chunk_size = Param.number(label="Chunk Size (words)", default=100, min=1)
    chunk_overlap = Param.number(label="Overlap Size (words)", default=10, min=0)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        col = ctx.parameters.get("column", "")
        size = int(ctx.parameters.get("chunk_size", 100))
        overlap = int(ctx.parameters.get("chunk_overlap", 10))
        return {"out": chunk_text_column(dataset, col, size, overlap)}


@node(name="Rename Columns", category="Transform", icon="Columns3", description="Rename specific dataset columns")
class RenameColumnsNode(Node):
    id = "rename_columns"
    in_data = Input.tabular(label="Rows")
    out = Output.tabular(label="Renamed Rows")
    
    mapping = Param.json(label="Rename Mapping (JSON)", default='{"old_name": "new_name"}', description="A JSON dictionary mapping old_name to new_name keys")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        mapping_str = ctx.parameters.get("mapping", "{}")
        import json
        mapping = json.loads(mapping_str)
        return {"out": rename_dataset_columns(dataset, mapping)}
