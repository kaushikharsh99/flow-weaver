# Getting Started with FlowWeaver

FlowWeaver is a visual desktop application and development workspace where you build and execute dataset cleaning graphs. By connecting nodes together, you compose a Directed Acyclic Graph (DAG) that processes inputs sequentially or in parallel.

---

## Core Visual Concepts

### 1. The Canvas
The central workspace where you lay out, connect, and configure nodes.
- **Pan / Zoom**: Hold middle-click or use scroll wheel to traverse the canvas.
- **Add Node**: Drag nodes from the left-hand Sidebar palette onto the canvas, or press `⌘K` / `Ctrl+K` to open the Command Palette search box.

### 2. Nodes & Ports
Each node represents a distinct preprocessing step (e.g. `Lowercase Text` or `Regex Replace`).
- **Inputs (Left handles)**: Receives dataset outputs from upstream nodes.
- **Outputs (Right handles)**: Produces datasets or tables passed to downstream nodes.
- **Port Types**: Color-coded to prevent invalid connections (e.g. Tabular columns match tabular inputs).

### 3. The Inspector
Selecting a node opens the Inspector sidebar on the right:
- **Parameters**: Node-specific settings (such as regex patterns, limit sizes, or output file paths).
- **Execution Profile**: Displays run duration (ms), peak memory allocation (Bytes), and throughput speed (rows/sec).
- **Edge Data Preview**: Renders a live 5-row sample table of output data and inferred column schemas.

---

## Your First Preprocessing Workflow

To clean a dataset:
1. **Load Data**: Drag a `Load CSV` node onto the canvas and select your source file path.
2. **Clean Text**: Drag a `Strip HTML` node, and connect `Load CSV (out)` → `Strip HTML (in_data)`.
3. **Filter**: Connect `Strip HTML` to a `Length Filter` node, setting the threshold parameter to limit story sizes.
4. **Save**: Connect `Length Filter` to `Write CSV` or `Write Parquet` and specify the output file path.
5. **Run**: Click the **Run** button in the upper toolbar. The canvas will stream execution statuses, highlighting active nodes in yellow, successful ones in green, and failures in red.
