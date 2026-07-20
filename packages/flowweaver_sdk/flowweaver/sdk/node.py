"""
FlowWeaver Declarative Node SDK

The dream:
    @node(name="Normalize Text", category="Text")
    class NormalizeText:
        text = Input.text()
        lowercase = Param.boolean(default=True)
        output = Output.text()
        def execute(self, ctx): ...

Everything is inferred. No registry. No frontend. No JSON.
"""
from typing import List, Dict, Any, Optional, Callable, Type
from .context import ExecutionContext


# ---------------------------------------------------------------------------
# Port descriptors — used as class-level attributes on a Node
# ---------------------------------------------------------------------------

class PortDescriptor:
    """Descriptor that declares an input or output port on a Node class."""
    def __init__(self, id: str, label: str, type: str, required: bool, direction: str):
        self.id = id
        self.label = label
        self.type = type
        self.required = required
        self.direction = direction  # "input" or "output"


class _InputFactory:
    """Factory for creating input port descriptors.

    Usage:
        class MyNode(Node):
            rows = Input.tabular(required=True)
            text = Input.text()
    """
    def tabular(self, label: str = "rows", required: bool = True) -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="tabular", required=required, direction="input")

    def text(self, label: str = "text", required: bool = True) -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="text", required=required, direction="input")

    def image(self, label: str = "image", required: bool = True) -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="image", required=required, direction="input")

    def audio(self, label: str = "audio", required: bool = True) -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="audio", required=required, direction="input")

    def any(self, label: str = "data", required: bool = False) -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="any", required=required, direction="input")


class _OutputFactory:
    """Factory for creating output port descriptors.

    Usage:
        class MyNode(Node):
            output = Output.tabular()
            result = Output.text()
    """
    def tabular(self, label: str = "rows") -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="tabular", required=False, direction="output")

    def text(self, label: str = "text") -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="text", required=False, direction="output")

    def image(self, label: str = "image") -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="image", required=False, direction="output")

    def audio(self, label: str = "audio") -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="audio", required=False, direction="output")

    def any(self, label: str = "data") -> PortDescriptor:
        return PortDescriptor(id="", label=label, type="any", required=False, direction="output")


# Singletons
Input = _InputFactory()
Output = _OutputFactory()


# ---------------------------------------------------------------------------
# Rich parameter descriptors — auto-generate frontend UI components
# ---------------------------------------------------------------------------

class ParamDescriptor:
    """Descriptor that declares a user-configurable parameter on a Node class."""
    def __init__(self, *, key: str = "", label: str = "", type: str,
                 default: Any = None, placeholder: str = "",
                 options: Optional[List[Dict[str, str]]] = None,
                 min: Optional[float] = None, max: Optional[float] = None,
                 step: Optional[float] = None, rows: int = 3,
                 accept: str = "", secret: bool = False,
                 description: str = ""):
        self.key = key
        self.label = label
        self.type = type
        self.default = default
        self.placeholder = placeholder
        self.options = options
        self.min = min
        self.max = max
        self.step = step
        self.rows = rows           # for textarea
        self.accept = accept       # for file (e.g. ".csv,.json")
        self.secret = secret       # for password/secret
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-friendly dict for API responses."""
        d: Dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "type": self.type,
        }
        if self.default is not None:
            d["default"] = self.default
        if self.placeholder:
            d["placeholder"] = self.placeholder
        if self.options:
            d["options"] = self.options
        if self.min is not None:
            d["min"] = self.min
        if self.max is not None:
            d["max"] = self.max
        if self.step is not None:
            d["step"] = self.step
        if self.type == "textarea" and self.rows != 3:
            d["rows"] = self.rows
        if self.accept:
            d["accept"] = self.accept
        if self.secret:
            d["secret"] = True
        if self.description:
            d["description"] = self.description
        return d


class _ParamFactory:
    """Factory for creating parameter descriptors.

    Usage:
        class MyNode(Node):
            path = Param.text(default="data/file.csv")
            threshold = Param.slider(min=0, max=1, step=0.01, default=0.5)
            lowercase = Param.boolean(default=True)
    """
    def text(self, label: str = "", default: str = "", placeholder: str = "", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="text", label=label, default=default, placeholder=placeholder, description=description)

    def textarea(self, label: str = "", default: str = "", placeholder: str = "", rows: int = 3, description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="textarea", label=label, default=default, placeholder=placeholder, rows=rows, description=description)

    def number(self, label: str = "", default: float = 0, min: Optional[float] = None, max: Optional[float] = None, step: Optional[float] = None, description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="number", label=label, default=default, min=min, max=max, step=step, description=description)

    def slider(self, label: str = "", default: float = 0, min: float = 0, max: float = 100, step: float = 1, description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="slider", label=label, default=default, min=min, max=max, step=step, description=description)

    def boolean(self, label: str = "", default: bool = False, description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="boolean", label=label, default=default, description=description)

    def select(self, label: str = "", default: str = "", options: Optional[List[Dict[str, str]]] = None, description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="select", label=label, default=default, options=options or [], description=description)

    def color(self, label: str = "", default: str = "#000000", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="color", label=label, default=default, description=description)

    def file(self, label: str = "", default: str = "", accept: str = "", placeholder: str = "", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="file", label=label, default=default, accept=accept, placeholder=placeholder, description=description)

    def regex(self, label: str = "", default: str = "", placeholder: str = "^pattern$", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="regex", label=label, default=default, placeholder=placeholder, description=description)

    def column(self, label: str = "", default: str = "", placeholder: str = "column_name", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="column", label=label, default=default, placeholder=placeholder, description=description)

    def secret(self, label: str = "", default: str = "", placeholder: str = "", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="secret", label=label, default=default, placeholder=placeholder, secret=True, description=description)

    def json(self, label: str = "", default: str = "{}", placeholder: str = "", rows: int = 5, description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="json", label=label, default=default, placeholder=placeholder, rows=rows, description=description)

    def expression(self, label: str = "", default: str = "", placeholder: str = "e.g. col_a + col_b", description: str = "") -> ParamDescriptor:
        return ParamDescriptor(type="expression", label=label, default=default, placeholder=placeholder, description=description)


# Singleton
Param = _ParamFactory()


# ---------------------------------------------------------------------------
# Port model (for serialization / backward compatibility)
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field as PydanticField


class Port(BaseModel):
    id: str
    label: str
    type: str  # tabular, text, image, audio, any
    required: bool = False

    class Config:
        populate_by_name = True


class Parameter(BaseModel):
    key: str
    label: str
    type: str
    default: Optional[Any] = None
    placeholder: Optional[str] = ""
    options: Optional[List[Dict[str, str]]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    rows: Optional[int] = None
    accept: Optional[str] = None
    secret: Optional[bool] = None
    description: Optional[str] = ""

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Node metaclass — introspects class attributes to build ports and parameters
# ---------------------------------------------------------------------------

# Global registry of all Node subclasses discovered
_NODE_CLASSES: List[Type] = []


class NodeMeta(type):
    """Metaclass that introspects PortDescriptor and ParamDescriptor attributes
    to automatically build the node's ports and parameter schema."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip the base Node class itself
        if name == "Node":
            return cls

        # Collect ports and parameters from class attributes
        inputs: List[Port] = []
        outputs: List[Port] = []
        params_schema: List[Parameter] = []

        # Also check if the class already has manually-set lists (backward compat)
        has_manual_inputs = isinstance(namespace.get("inputs"), list) and all(isinstance(p, Port) for p in namespace.get("inputs", []))
        has_manual_outputs = isinstance(namespace.get("outputs"), list) and all(isinstance(p, Port) for p in namespace.get("outputs", []))
        has_manual_params = isinstance(namespace.get("params_schema"), list)

        if not has_manual_inputs or not has_manual_outputs:
            for attr_name, attr_val in namespace.items():
                if isinstance(attr_val, PortDescriptor):
                    port_id = attr_val.id if attr_val.id else attr_name
                    port = Port(id=port_id, label=attr_val.label, type=attr_val.type, required=attr_val.required)
                    if attr_val.direction == "input":
                        inputs.append(port)
                    else:
                        outputs.append(port)

            if inputs and not has_manual_inputs:
                cls.inputs = inputs
            if outputs and not has_manual_outputs:
                cls.outputs = outputs

        if not has_manual_params:
            for attr_name, attr_val in namespace.items():
                if isinstance(attr_val, ParamDescriptor):
                    attr_val.key = attr_val.key if attr_val.key else attr_name
                    attr_val.label = attr_val.label if attr_val.label else attr_name.replace("_", " ").title()
                    params_schema.append(Parameter(
                        key=attr_val.key,
                        label=attr_val.label,
                        type=attr_val.type,
                        default=attr_val.default,
                        placeholder=attr_val.placeholder,
                        options=attr_val.options,
                        min=attr_val.min,
                        max=attr_val.max,
                        step=attr_val.step,
                        rows=attr_val.rows if attr_val.type in ("textarea", "json") else None,
                        accept=attr_val.accept if attr_val.type == "file" else None,
                        secret=attr_val.secret if attr_val.secret else None,
                        description=attr_val.description,
                    ))
            if params_schema:
                cls.params_schema = params_schema

        # Auto-register this class so the registry can discover it
        if hasattr(cls, "id") and cls.id:
            _NODE_CLASSES.append(cls)

        return cls


# ---------------------------------------------------------------------------
# Base Node class
# ---------------------------------------------------------------------------

class Node(metaclass=NodeMeta):
    """Base Node class that plugin builders inherit from.

    Nodes are self-describing. All metadata lives on the class:
        id, label, category, description, icon, color,
        inputs, outputs, params_schema, documentation, examples, tags, version

    Lifecycle methods:
        execute(inputs, ctx)  — required, runs the node
        preview(inputs, ctx)  — optional, lightweight preview for the UI
        validate(ctx)         — optional, validates parameters before execution
    """
    id: str = ""
    label: str = ""
    category: str = ""
    description: str = ""
    icon: str = "Wand2"
    color: str = "#7a4fc6"
    version: str = "1.0.0"
    tags: List[str] = []

    inputs: List[Port] = []
    outputs: List[Port] = []
    params_schema: List[Parameter] = []

    # Self-documenting metadata
    documentation: str = ""  # Markdown documentation
    examples: List[Dict[str, Any]] = []  # Example configurations

    def execute(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Dict[str, Any]:
        """Execute implementation. Accepts inputs and returns dictionary mapping output port -> value."""
        raise NotImplementedError("execute() must be implemented by subclasses.")

    def compile(self, ctx: Any) -> Any:
        """Compile implementation. Generates Intermediate Representation (IR) call/expression for this node."""
        return None

    def preview(self, inputs: Dict[str, Any], ctx: ExecutionContext) -> Optional[Dict[str, Any]]:

        """Optional lightweight preview for the UI. Returns same shape as execute().
        If not implemented, the framework falls back to execute()."""
        return None

    def validate(self, ctx: ExecutionContext) -> List[str]:
        """Optional parameter validation. Returns a list of error messages (empty = valid)."""
        return []

    def dict(self, by_alias: bool = False) -> Dict[str, Any]:
        """Serialize this node's full metadata to a JSON-friendly dictionary."""
        result: Dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "version": self.version,
            "tags": self.tags,
            "inputs": [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in self.inputs],
            "outputs": [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in self.outputs],
            "params_schema": [p.model_dump(exclude_none=True) if hasattr(p, "model_dump") else p.dict(exclude_none=True) for p in self.params_schema],
        }
        if self.documentation:
            result["documentation"] = self.documentation
        if self.examples:
            result["examples"] = self.examples
        return result


# ---------------------------------------------------------------------------
# @node decorator — the dream API
# ---------------------------------------------------------------------------

def node(*, name: str = "", category: str = "", description: str = "",
         icon: str = "Wand2", color: str = "", version: str = "1.0.0",
         tags: Optional[List[str]] = None, documentation: str = ""):
    """Decorator that configures a Node class with metadata.

    Usage:
        @node(name="Normalize Text", category="Text", icon="Type")
        class NormalizeText(Node):
            text = Input.text()
            lowercase = Param.boolean(default=True)
            output = Output.text()

            def execute(self, inputs, ctx):
                ...
    """
    # Default category colors
    CAT_COLORS = {
        "Loaders": "#4f86c6", "Filters": "#c67a4f", "Transform": "#7a4fc6",
        "Dedup": "#4fc6a0", "NLP": "#c64f86", "Export": "#c6b74f",
        "Text": "#c64f86", "AI": "#c64f86", "Vision": "#4f86c6",
        "Audio": "#c67a4f", "Data": "#7a4fc6",
    }

    def decorator(cls: Type) -> Type:
        # Infer id from class name if not set: NormalizeText -> normalize_text
        if not cls.id:
            cls.id = "".join(
                f"_{c.lower()}" if c.isupper() and i > 0 else c.lower()
                for i, c in enumerate(cls.__name__)
            )
        if name:
            cls.label = name
        elif not cls.label:
            # CamelCase -> spaced: NormalizeText -> Normalize Text
            cls.label = "".join(
                f" {c}" if c.isupper() and i > 0 else c
                for i, c in enumerate(cls.__name__)
            ).strip()
        if category:
            cls.category = category
        if description:
            cls.description = description
        elif not cls.description:
            cls.description = cls.__doc__ or f"A {cls.label} node."
        if icon:
            cls.icon = icon
        if color:
            cls.color = color
        elif not cls.color or cls.color == "#7a4fc6":
            cls.color = CAT_COLORS.get(cls.category, "#7a4fc6")
        if version:
            cls.version = version
        if tags:
            cls.tags = tags
        if documentation:
            cls.documentation = documentation

        return cls

    return decorator


# ---------------------------------------------------------------------------
# Discovery helper — returns all registered Node classes
# ---------------------------------------------------------------------------

def get_discovered_nodes() -> List[Type]:
    """Returns all Node subclasses that have been imported and registered via metaclass."""
    return list(_NODE_CLASSES)
