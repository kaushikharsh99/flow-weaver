# FlowWeaver Project Roadmap (v1.0)

**Vision:** FlowWeaver is an open-source visual preprocessing platform for AI datasets. 
We focus exclusively on providing a stellar data cleaning, filtering, tokenizing, and restructuring experience for AI/ML researchers. Out of scope for v1.0: workflow orchestrators, complex cloud scheduling, auth/RBAC, marketplaces, billing, and distributed cluster scheduling.

---

## Roadmap Phases

```mermaid
gantt
    title FlowWeaver v1.0 Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  Phase %q
    
    section Core Infrastructure
    Phase 1: Freeze the Foundation     :done, a1, 2026-07-01, 20d
    Phase 2: Frictionless Development   :done, a2, after a1, 20d
    Phase 3: Framework Quality          :done, a3, after a2, 30d
    
    section Node Library & Templates
    Phase 4: First Real Node Collection :done, b1, after a3, 30d
    Phase 5: Out-of-the-Box Templates   :done, b2, after b1, 20d
    
    section Publishing & Polish
    Phase 6: Documentation Website      :active, c1, after b2, 20d
    Phase 7: Team Expansion & Scaling   :c2, after c1, 20d
    Phase 8: Polish & Previews          :c3, after c2, 15d
    Phase 9: Public Alpha Release       :c4, after c3, 15d
```

---

## Detailed Roadmap Phases

### Phase 1 — Freeze the Foundation
**Goal:** Freeze the API specs and engine core to prevent downstream breaking changes.
* **APIs to Freeze:**
  - Declarative Node SDK & Node metaclass decorator
  - Workspace directory auto-discovery & loading
  - REST & WebSocket communication contracts
  - Visual Compiler subsystem and pipeline package generators
  - `Dataset` abstract base layers (Tabular, Polars, Arrow, Streaming)
* **Status:** Complete.

---

### Phase 2 — Frictionless Node Development
**Goal:** Ensure external developers can construct nodes quickly and independently.
* **Deliverables:**
  - One CLI command (`flowweaver create-node`) to generate the full "Node-as-Adapter" layout.
  - Automatic directory scanning and registration (zero code config).
  - Backend configuration properties auto-generating visual UI inputs in the frontend Inspector.
  - Automatic documentation (`flowweaver generate-docs`) and test scaffolds.
  - Better templates for Loader, Filter, Transform, and Exporter categories.
  - Pre-packaging validation schemas.
* **Status:** Complete.

---

### Phase 3 — Framework Quality
**Goal:** Elevate compiler telemetry, exception handling, and error routing for researchers.
* **Deliverables:**
  1. **Better Error System:** Format exceptions showing Node context, exact problem, current state, and action recommendation (e.g. Column "text" not found).
  2. **Better Logging & Timing:** Timed execution summaries (`time.time()`) and standard `logging` setup in generated Python output.
  3. **Progress System:** Structured progress comments injected for every pipeline step (e.g., `logger.info("Step 3/8: Normalize Text to Lowercase")`).
  4. **Preview Engine:** Render dataset columns, schema, row counts, and memory footprint in the frontend Inspector dynamically.
  5. **Pre-Run Validation**: Kahn's sorter cycle checks and parameter validation prior to compilation.
* **Status:** Complete.

---

### Phase 4 — First Real Node Collection
**Goal:** Hand-craft 20 high-fidelity nodes representing typical AI dataset cleaning tasks.
* **Loaders:** CSV, JSON, JSONL, Parquet
* **Cleaning:** Lowercase, Uppercase, Strip HTML, Remove Empty, Unicode Normalize, Regex Replace, Strip Whitespace
* **Filters:** Generic Filter, Length Filter, Duplicate Filter (xxHash, SimHash near-duplicate, MinHash Jaccard sets)
* **Transform:** Select Columns, Rename Columns, Drop Columns, Sort Rows, Shuffle, Split Dataset, Concatenate, Statistics
* **Export:** CSV, JSONL, Parquet
* **Status:** Complete.

---

### Phase 5 — Templates Gallery
**Goal:** Ship out-of-the-box pipeline templates so researchers don't start with a blank canvas.
* **Included Templates:**
  - LLM Fine-Tuning Prep
  - Retrieval Augmented Generation (RAG) Document Parser
  - TinyStories Dataset Cleaning
  - ShareGPT Preprocessing
  - OCR Output Post-Processing
  - Common Crawl Filtering
* **Status:** Complete.

---

### Phase 6 — Documentation Website
**Goal:** Deploy a clean, accessible docs portal containing guides, FAQs, and API definitions.
* **Sections:** Getting Started, Installation, Architecture, SDK reference, Creating Nodes, Plugin Development, Examples, CLI reference.

---

### Phase 7 — Team Expansion
**Goal:** Onboard the core team to develop nodes and pipeline templates under standard rules.
* **Separation of Work:**
  - *Core Architects:* SDK, compiler, graph optimizer, runner runtime.
  - *Team Contributors:* Custom nodes, dataset cleaning plugins, benchmarks, guides.

---

### Phase 8 — User Experience Polish
**Goal:** Deliver small quality-of-life enhancements that make the tool feel premium.
* **Polish areas:** Interactive canvas performance, keyboard shortcuts, canvas undo/redo, responsive search, empty-state helpers, node search icons.

---

### Phase 9 — Public Alpha
**Goal:** Release FlowWeaver to the AI researcher community.
* **Action:** Collect telemetry and usage metrics, fix performance bottlenecks on real-world multi-gigabyte datasets, and iterate the design.
