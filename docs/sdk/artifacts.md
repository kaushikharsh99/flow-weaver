# FlowWeaver Artifacts SDK Guide

Artifacts are non-dataset outputs produced during a pipeline run. Examples include generated files (PDF report, exported CSV), trained machine learning model files, charts (PNG/SVG plots), and serialized metadata logs.

Artifacts are registered under an execution run and can be inspected/downloaded in the visual workspace.

---

## Writing Artifacts from Nodes

Every artifact must be registered through `ExecutionContext.artifacts` so that FlowWeaver can track and store it:

```python
from flowweaver.sdk import Node, node, ExecutionContext
import time

@node(name="PDF Exporter", category="Export")
class PdfExportNode(Node):
    def execute(self, inputs, ctx: ExecutionContext):
        # Generate the PDF file in a temporary folder
        output_path = "/tmp/report_123.pdf"
        self._build_pdf(output_path)
        
        # Register artifact
        ctx.artifacts.create(
            name="Monthly Analysis Report",
            filepath=output_path,
            mime_type="application/pdf",
            metadata={
                "page_count": 5,
                "file_size_bytes": os.path.getsize(output_path)
            }
        )
        return {}
```

---

## Artifact Properties

When registering an artifact, provide:
- **name**: Human-readable label displayed in the UI inspector list.
- **filepath**: Absolute path where the file is stored. FlowWeaver will copy this file into the permanent run storage workspace.
- **mime_type**: Used by the web app to choose the correct preview renderer (e.g. `image/png`, `application/pdf`, `text/markdown`, `application/json`).
- **metadata**: Key-value data that stores summary metrics, row counts, model accuracy, etc.

---

## Auto-discovered Outputs vs Artifacts
- **Tabular Outputs** (ports) should flow to downstream nodes.
- **Artifacts** are the *end products* of a pipeline, designed for humans to download, view, or upload to external systems.
