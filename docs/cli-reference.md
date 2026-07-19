# CLI Reference Guide

The `flowweaver` command-line utility provides tools to scaffold, test, lint, and package nodes and plugins.

---

## Command List

```
flowweaver [command] [options]
```

| Command | Description |
|---|---|
| [`create-plugin`](#create-plugin) | Scaffold a new dynamic plugin workspace template |
| [`create-node`](#create-node) | Scaffold a single node capability package |
| [`test-node`](#test-node) | Run local tests against example json configurations |
| [`lint-node`](#lint-node) | Enforce metaclass properties, style rules, and limits |
| [`generate-docs`](#generate-docs) | Automatically generate Markdown documentation |
| [`package-plugin`](#package-plugin) | Compile into tar.gz with integrity checksum manifest |

---

## Command Reference

### `create-plugin`
Generates a new multi-node plugin folder structure.
```bash
flowweaver create-plugin my_plugin_name
```
* **Output**: Creates a new folder with `plugin.yaml`, `requirements.txt`, and a package package boilerplate.

---

### `create-node`
Generates a capability directory with category-specific adapters, service layers, tests, benchmarks, and data.
```bash
flowweaver create-node NodeName --category [Loader|Filter|Transform|Exporter|AI|Custom]
```
* `--category`: Configures appropriate default ports and parameters.
* **Output**: Sets up `node.py`, `service.py`, `core/algorithm.py`, `utils/helpers.py`, `tests/`, `examples/`, `benchmarks/`, and `data/` sample files.

---

### `test-node`
Executes node tests against mock configurations.
```bash
flowweaver test-node ./plugins/my_node
```
* **Output**: Runs `execute()` with parameters imported from `examples/basic.json` and outputs a `PASS` or `FAIL` status report.

---

### `lint-node`
Validates that the node meets strict design and security specifications.
```bash
flowweaver lint-node ./plugins/my_node
```
* **Checks Enforced**:
  - `node.py` is under 200 lines.
  - No direct forbidden imports (`requests`, `threading`, `sqlite3`, `logging`, `urllib`, `subprocess`).
  - Required attributes (`id`, `label`, `category`, `description`) are declared.
  - Required ports and parameters are configured.

---

### `generate-docs`
Generates Markdown reference files from node metaclass declarations.
```bash
flowweaver generate-docs ./plugins/my_node
```
* **Output**: Creates a `docs.md` document detailing inputs/outputs, parameter schemas (default value/types), and description fields.

---

### `package-plugin`
Packs a verified plugin folder into a tar archive.
```bash
flowweaver package-plugin ./plugins/my_plugin
```
* **Sequence**: Automatically executes `lint-node` first. Aborts if lint validations fail.
* **Output**: Produces `<plugin_name>.tar.gz` and `manifest.json` with SHA-256 integrity hashes.
