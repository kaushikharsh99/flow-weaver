import os
from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from app.engine.nodes.core_logic import write_jsonl_file, write_parquet_file, upload_hf_hub_dataset

@node(name="Write CSV", category="Export", icon="Save", description="Serialize records to a CSV file")
class WriteCSVNode(Node):
    id = "write_csv"
    in_data = Input.tabular(label="Rows")
    
    path = Param.file(label="Output path", default="out/results.csv", accept=".csv")
    compress = Param.boolean(label="Gzip compression", default=False)

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
            
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
            
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        import csv
        columns = dataset.columns()
        rows_dicts = dataset.to_list()
        
        with open(path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if columns:
                writer.writerow(columns)
            for row in rows_dicts:
                writer.writerow([row.get(col, "") for col in columns])
        return {}


@node(name="Write JSON Lines", category="Export", icon="Download", description="Serialize dataset records into JSON Lines format")
class WriteJSONLNode(Node):
    id = "write_jsonl"
    in_data = Input.tabular(label="Rows")
    path = Param.file(label="Output path", default="out/results.jsonl", accept=".jsonl")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
        write_jsonl_file(dataset, path)
        return {}


@node(name="Write Parquet", category="Export", icon="FolderArchive", description="Serialize dataset records into Parquet format using Polars")
class WriteParquetNode(Node):
    id = "write_parquet"
    in_data = Input.tabular(label="Rows")
    path = Param.file(label="Output path", default="out/results.parquet", accept=".parquet")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
        path = ctx.parameters.get("path", "")
        for k, v in ctx.variables.items():
            path = path.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
        write_parquet_file(dataset, path)
        return {}


@node(name="Upload HuggingFace", category="Export", icon="Globe", description="Upload dataset repository directly to Hugging Face Hub")
class UploadHFDatasetNode(Node):
    id = "upload_hf_dataset"
    in_data = Input.tabular(label="Rows")
    
    repo_id = Param.text(label="Repository ID", default="username/dataset_name", placeholder="e.g. myprofile/my-preprocessed-dataset")
    split = Param.text(label="Target Split", default="train")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        dataset = inputs.get("in_data")
        if not dataset:
            return {}
        repo_id = ctx.parameters.get("repo_id", "username/dataset_name")
        split = ctx.parameters.get("split", "train")
        hf_url = upload_hf_hub_dataset(dataset, repo_id, split)
        ctx.log(f"Dataset successfully uploaded. View at: {hf_url}")
        return {}
