# FlowWeaver Parameter Guide

FlowWeaver parameters define the user configuration variables for each node. Declaring a parameter on a python Node class auto-generates the corresponding UI input component in the visual Inspector without requiring any frontend React code.

---

## The 13 Parameter Types

### 1. `Param.text()`
Creates a simple text input box.
```python
name = Param.text(label="User Name", default="Anonymous", placeholder="Enter name")
```

### 2. `Param.textarea()`
Creates a multi-line text input field.
```python
query = Param.textarea(label="Raw Query", default="", rows=4)
```

### 3. `Param.number()`
Creates a numeric input field with min, max, and step boundaries.
```python
count = Param.number(label="Fetch Limit", default=100, min=1, max=10000)
```

### 4. `Param.slider()`
Creates a range slider.
```python
threshold = Param.slider(label="Fuzzy Threshold", default=80, min=0, max=100, step=1)
```

### 5. `Param.boolean()`
Creates a simple toggle switch.
```python
compress = Param.boolean(label="Compress Output", default=False)
```

### 6. `Param.select()`
Creates a dropdown select list.
```python
format = Param.select(label="Format", default="json", options=[
    {"label": "JSON Array", "value": "json"},
    {"label": "CSV File", "value": "csv"}
])
```

### 7. `Param.color()`
Creates a color picker.
```python
color_theme = Param.color(label="Node Color", default="#7a4fc6")
```

### 8. `Param.file()`
Creates a file path text input with optional extensions helper.
```python
source_path = Param.file(label="Source File", default="", accept=".csv,.json")
```

### 9. `Param.regex()`
Creates a regex input styled with monospace boundaries and verification.
```python
match_pattern = Param.regex(label="Filter Pattern", default="^error.*")
```

### 10. `Param.column()`
Creates a column mapper text input styled with a database/table column icon.
```python
join_col = Param.column(label="Key Column", default="id")
```

### 11. `Param.secret()`
Creates a password input that hides characters and turns off client-side logging.
```python
api_key = Param.secret(label="API Token", placeholder="Enter secret token")
```

### 12. `Param.json()`
Creates a structured JSON textarea with monospace rendering and validation.
```python
headers = Param.json(label="Request Headers", default='{"Content-Type": "application/json"}')
```

### 13. `Param.expression()`
Creates a mathematical or row expression editor with `fx` rendering.
```python
formula = Param.expression(label="Formula", default="col_a + col_b")
```

---

## Options Metadata

All parameter types accept these universal attributes:
- `label`: Overrides default attribute-to-spaced-title labeling.
- `default`: The fallback configuration value.
- `description`: Sub-hint rendered in the Inspector to explain the parameter.

---

## Validation & Coercion
The validation engine verifies input types at execution start. If a number parameters receives string characters, validation returns errors before executing the pipeline.
