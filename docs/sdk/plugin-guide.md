# FlowWeaver Plugin Developer Guide

Plugins are the packaging mechanism for introducing new capabilities to FlowWeaver. A plugin can declare one or more nodes, packages of core algorithms, assets, benchmarks, and example flows.

---

## Folder Layout

FlowWeaver enforces a strict layered directory structure to separate visual integration interfaces from core computational logic:

```
plugins/
    category/
        plugin_name/
            plugin.yaml         # Plugin manifest
            README.md           # Plugin documentation
            requirements.txt    # Third-party pip packages
            node.py             # Thin FlowWeaver interface adapter (under 200 lines)
            service.py          # Service orchestration layer (optional)
            
            core/               # Pure computational algorithms
                __init__.py
                algorithm.py
                
            utils/              # Auxiliary subroutines / helpers
                __init__.py
                helpers.py
                
            tests/              # Test suite separating adapter from algorithm
                __init__.py
                test_node.py
                test_algorithm.py
                test_examples.py
                
            examples/           # Example flows / json parameter fixtures
                basic.json
                advanced.json
                
            benchmarks/         # Performance benchmarks
                __init__.py
                benchmark.py
```

---

## Plugin Manifest (`plugin.yaml`)

Every plugin folder must contain a `plugin.yaml` manifest file at its root specifying metadata and entrypoint nodes:

```yaml
id: text_processor
name: Text Processor Plugin
version: 0.1.0
author: FlowWeaver Team
description: Text clean-up and tokenization capability pack.
nodes:
  # Path from the plugin root package to the Node class
  - node.NormalizeTextNode
  - node.TokenizeTextNode
```

---

## Managing Dependencies (`requirements.txt`)

If your core algorithm or utility packages require external third-party python modules (e.g. `numpy`, `spacy`, `polars`), list them in the plugin's `requirements.txt`:

```text
polars>=0.20.0
spacy>=3.7.0
```

> [!NOTE]
> FlowWeaver handles isolation by installing these requirements into the engine's virtual environment or sandboxed runner when a plugin is registered/installed.

---

## Packaging Plugins via CLI

Use the FlowWeaver CLI suite to manage your plugin packages:

### 1. Lint and Verify Node
Ensure your node class meets style guide parameters, does not exceed the line limit, and does not contain unauthorized imports:
```bash
flowweaver lint-node ./plugins/my_plugin
```

### 2. Package Plugin
Build a `.tar.gz` distribution file and metadata checksum manifest for deployment:
```bash
flowweaver package-plugin ./plugins/my_plugin
```

---

## Best Practices
- **Logical Grouping**: Group related nodes (e.g. `Dedup Exact` and `Dedup Fuzzy`) into a single plugin package sharing the same `core/` modules.
- **Pure Core**: Keep files inside `core/` completely pure and generic so they can be run in any Python application without FlowWeaver dependencies.
