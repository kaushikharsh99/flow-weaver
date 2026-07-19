# FlowWeaver Node Developer Guide

Nodes are **adapters** that bridge the FlowWeaver execution engine with the core business and computational algorithms. They define *what* inputs, outputs, and configuration parameters are exposed to the visual builder and the runtime compiler.

> [!IMPORTANT]
> **Nodes are adapters, not business logic implementations.**
> Keep `node.py` under 200 lines. All core computational logic belongs in independent Python packages (e.g., inside `core/` or `engine/`).

---

## The Node Lifecycle

1. **Discovery & Import**: The registry scans the engine directories and plugin paths, importing subclasses of `Node` on startup.
2. **UI Synchronization**: Class attributes (Input, Output, Param descriptors) are introspected via metaclass and exposed as a JSON Schema to the web client via `GET /api/nodes`.
3. **Validation**: Before running, configuration values are validated against the node's schema.
4. **Execution**: The compiler invokes the node's `execute()` method with resolved inputs and parameters in a thread-safe execution context.

---

## Defining a Node Class

Use the `@node` decorator to declare a node class:

```python
from typing import Dict, Any
from flowweaver.sdk import Node, Input, Output, Param, node, ExecutionContext
from service import TextProcessingService

@node(
    name="Normalize Text",
    category="Text",
    icon="Type",
    description="Normalize text cases, spaces, and encoding.",
    version="1.0.0"
)
class NormalizeTextNode(Node):
    # Ports (Inputs & Outputs)
    in_text = Input.text(label="Input Text")
    out_text = Output.text(label="Normalized Text")

    # Parameters
    lowercase = Param.boolean(label="Lowercase", default=True, description="Convert text to lowercase")
    strip_whitespace = Param.boolean(label="Strip Space", default=True, description="Remove outer whitespace")

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        """Node adapter execution.
        Must remain thin and delegate to core algorithms.
        """
        text_val = inputs.get("in_text", "")
        service = TextProcessingService()
        
        normalized = service.normalize(
            text_val, 
            lowercase=ctx.parameters.get("lowercase", True),
            strip_ws=ctx.parameters.get("strip_whitespace", True)
        )
        return {"out_text": normalized}
```

---

## Declaring Ports

Ports are defined using the `Input` and `Output` descriptor factories:
- `Input.tabular(label, required)` / `Output.tabular(label)`
- `Input.text(label, required)` / `Output.text(label)`
- `Input.image(label, required)` / `Output.image(label)`
- `Input.audio(label, required)` / `Output.audio(label)`
- `Input.any(label, required)` / `Output.any(label)`

---

## Declaring Parameters

Parameters declare configuration inputs rendered dynamically in the frontend Inspector. 
- Refer to [Parameters Guide](parameters.md) for the 13 supported parameter types (`Param.text`, `Param.slider`, `Param.secret`, etc.).

---

## Execution Lifecycle Methods

### 1. `execute(inputs, ctx)`
Runs during the pipeline execution stage.
- **Inputs**: A dictionary mapping input port IDs to their values.
- **Context**: An `ExecutionContext` instance containing parameters, environment variables, logger, and system services.
- **Returns**: A dictionary mapping output port IDs to their values.

### 2. `preview(inputs, ctx)`
An optional lightweight preview function invoked by the frontend to render mock preview results before a complete pipeline run.
- Should calculate a small, fast subset of the output (e.g. processing only the first 5 rows of a dataset).

### 3. `validate(ctx)`
An optional validation helper that returns a list of string validation errors if parameters are invalid.
- Return an empty list `[]` if the configuration is correct.

---

## Best Practices
- **Thin Adapters**: Keep `node.py` under 200 lines.
- **No Side Effects**: Never call `os`, `requests`, `threading`, or standard logging modules directly inside `node.py`. Route all operations through `ExecutionContext`.
- **Stateless**: Do not keep mutable state on the Node class instance. It must be thread-safe.
