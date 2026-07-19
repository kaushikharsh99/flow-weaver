# Plugin Development Guide

Plugins are packages containing a grouping of capability nodes, assets, and third-party dependencies designed to extend FlowWeaver's preprocessing palette.

---

## 1. Plugin Folder Structure

A plugin contains a folder housing a `plugin.yaml` manifest config and one or more node modules:

```
plugins/
    nlp_pack/
        plugin.yaml         # Config manifest
        README.md
        requirements.txt    # External library dependencies
        nlp_pack/           # Python package name matching id
            __init__.py
            nodes.py        # Exposes the Node classes
            core/           # Business logic packages
            utils/
```

---

## 2. Manifest Schema (`plugin.yaml`)

The `plugin.yaml` file tells FlowWeaver's engine registry how to parse and register your custom extensions on boot:

```yaml
id: nlp_pack
name: NLP Processing Extensions
version: 0.2.1
author: Research Group
description: Advanced tokenizers and sentiment analysers.
nodes:
  # Imports NLPNode class from nlp_pack.nodes module
  - nlp_pack.nodes.NLPNode
```

### Manifest properties:
* `id` (str): Unique alphanumeric string identifier.
* `name` (str): Label displayed in the registry portal.
* `nodes` (List[str]): Paths to subclasses of `Node` within the package.

---

## 3. Managing Requirements (`requirements.txt`)

If your core packages import external libraries (such as `scikit-learn` or `nltk`), add them to the plugin's `requirements.txt`:

```text
scikit-learn>=1.4.0
nltk>=3.8.1
```

FlowWeaver's engine installer handles dynamic dependency resolution during deployment.

---

## 4. Distributing Plugins

### Step A: Package
Compile the plugin directory into a distributable archive file containing files and SHA-256 hashes:
```bash
flowweaver package-plugin ./plugins/nlp_pack
```
This generates:
- `nlp_pack.tar.gz`: Compressed plugin bundle.
- `manifest.json`: Verification manifest.

### Step B: Install
Install the plugin archive into the FlowWeaver environment (or add to `plugins/` directory where it is auto-discovered).
