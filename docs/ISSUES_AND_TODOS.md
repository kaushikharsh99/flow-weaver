# FlowWeaver Outstanding Issues, Bugs & Future Backlog

This document maintains a comprehensive backlog of remaining stubs, visual synchronization gaps, and performance optimizations. Maintainers can assign these tasks to team contributors during Phase 7 scaling.

---

## 1. Unimplemented Core Node Stubs (Highest Priority)
Currently, several nodes exist as placeholder stubs in [stubs.py](file:///home/harsh/coding/flow-weaver/apps/api/app/engine/nodes/stubs.py). These need to be converted to thin adapters wrapping robust capabilitiy modules:

### Data Loaders & Exporters
- [ ] **S3 Bucket Loader (`load_s3`)**: Needs to connect to boto3, download datasets securely, and return streaming chunks.
- [ ] **SQL Query (`load_sql`)**: Needs to connect to SQLAlchemy engines and stream relational rows as datasets.
- [ ] **Load Images (`load_images`)**: Needs to load raw images, track byte streams, and return `ImageDataset` wrappers.
- [ ] **HTTP Fetch (`http_fetch`)**: Needs to query public web endpoints using ExecutionContext-secured requests.
- [ ] **Upload S3 (`upload_s3`)**: Needs to stream output Parquet/CSV back to AWS S3.
- [ ] **Send Webhook (`webhook`)**: Needs to POST final dataset summaries or records to API callbacks.

### Filtering & Cleaning
- [ ] **Fuzzy Deduplication (`dedup_fuzzy`)**: Needs to implement MinHash/LSH with band bucketing, or Levenshtein distance matrices for non-text tabular fields.
- [ ] **Sample Rows (`sample_rows`)**: Needs to support random sampling, stratified sampling, or head/tail record slices.

### Transformers & Aggregators
- [ ] **Map Expression (`map_expr`)**: Needs to parse and evaluate mathematical/string expressions securely (e.g. `col["age"] + 1`) without exposing the host to unsafe Python `eval` vulnerabilities.
- [ ] **Join Rows (`join_rows`)**: Needs to merge two input datasets (left, right, inner) based on key fields.
- [ ] **Sort Rows (`sort_rows`)**: Needs to sort rows ascending/descending by column.
- [ ] **Select Columns (`select_columns`)**: Needs to filter out unwanted headers.
- [ ] **Split Column (`split_col`)**: Needs to split strings by delimiters into list arrays.

### AI & Semantic Processors
- [ ] **Generate Embeddings (`embed_text`)**: Needs to call embedding model APIs (OpenAI/Gemini/HuggingFace) using rate-limiting chunk retries.
- [ ] **Sentiment Classifier (`sentiment`)**: Needs to classify rows using small offline classifiers or API endpoints.
- [ ] **Summarize (`summarize`)**: Needs to summarize large texts using LLM integrations.
- [ ] **Detect Language (`detect_lang`)**: Needs to use fast, offline language identifier packages (like `fasttext` or `langdetect`).

---

## 2. Visual Synchronization & REST Gaps

### Debugger Pause/Resume Controls
- **Issue**: Pause, Resume, and Stop canvas toolbar buttons do not fully target backend pause endpoints in production mode.
- **Task**: Update the frontend runner [runner.ts](file:///home/harsh/coding/flow-weaver/apps/web/src/pipeline/runner.ts) to fire `POST /api/executions/{id}/pause` and `POST /api/executions/{id}/resume` REST queries when running in `VITE_USE_MOCK_API=false`.

### WebSocket Logging Card Auto-scroll
- **Issue**: The logging console card in the visual canvas continues accumulating logs, but does not auto-scroll to the bottom.
- **Task**: Add an auto-scroll anchor ref to the terminal log container in [Inspector.tsx](file:///home/harsh/coding/flow-weaver/apps/web/src/pipeline/components/Inspector.tsx).

### Pipeline Auto-Save
- **Issue**: Canvas state changes (dragging nodes, adding connections) are saved to the Zustand store, but not auto-saved to the database server. If the user refreshes, edits are lost.
- **Task**: Implement a debounced auto-save hook that triggers `savePipelineToServer()` 1-2 seconds after the last canvas modification.

---

## 3. Core Engine Bugs & Gaps

### Pipeline Parameter Variables
- **Bug**: The compiler schema parses pipeline-level variables (e.g. `${API_KEY}`), but the backend executing engine runner does not dynamically replace these string templates in node parameters prior to execution.
- **Fix**: Update `runner.py`'s node compilation stage to scan parameter values and substitute matching global variables.

### Checkpoint Caching Optimization
- **Bug**: The optimizer parses checkpoint flags, but the execution runner currently runs all nodes sequentially regardless of cache status.
- **Fix**: Store dataset hashes of node inputs. If inputs and parameters are identical to the previous run, load the output from disk caches rather than re-running the node.

### Windows / Docker Port Collisions
- **Issue**: Standard port `8080` (frontend) and `8000` (backend) are commonly taken on developer machines.
- **Task**: Modify `docker-compose.yml` to map host ports to `.env` variables (e.g. `FLOWWEAVER_PORT_WEB`, `FLOWWEAVER_PORT_API`) to support customization out-of-the-box.
