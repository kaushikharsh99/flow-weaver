import { toast } from "sonner";
import { NODE_TYPE_MAP } from "./nodeTypes";
import type { PipelineNode } from "./store";
import { useStore } from "./store";
import type { Edge } from "reactflow";
import {
  MOCK_EXECUTION_MIN_DELAY_MS,
  MOCK_EXECUTION_MAX_DELAY_MS,
  MOCK_ERROR_RATE
} from "./constants";
import { api, isMockMode } from "../api";

function topoSort(nodes: PipelineNode[], edges: Edge[]): { order: string[][]; error?: string } {
  const indeg = new Map<string, number>();
  const adj = new Map<string, string[]>();
  for (const n of nodes) { indeg.set(n.id, 0); adj.set(n.id, []); }
  for (const e of edges) {
    if (!indeg.has(e.source) || !indeg.has(e.target)) continue;
    adj.get(e.source)!.push(e.target);
    indeg.set(e.target, (indeg.get(e.target) || 0) + 1);
  }
  const layers: string[][] = [];
  let frontier = nodes.filter(n => (indeg.get(n.id) || 0) === 0).map(n => n.id);
  const seen = new Set<string>();
  while (frontier.length) {
    layers.push(frontier);
    frontier.forEach(id => seen.add(id));
    const next: string[] = [];
    for (const id of frontier) {
      for (const t of adj.get(id) || []) {
        indeg.set(t, (indeg.get(t) || 1) - 1);
        if (indeg.get(t) === 0) next.push(t);
      }
    }
    frontier = next;
  }
  if (seen.size !== nodes.length) return { order: [], error: "Cycle detected in pipeline graph" };
  return { order: layers };
}

function validate(nodes: PipelineNode[], edges: Edge[]): { ok: boolean; problem?: { nodeId: string; msg: string } } {
  const incoming = new Map<string, Set<string>>();
  for (const e of edges) {
    if (!incoming.has(e.target)) incoming.set(e.target, new Set());
    if (e.targetHandle) incoming.get(e.target)!.add(e.targetHandle);
  }
  for (const n of nodes) {
    if (n.type === "commentNode") continue;
    const def = NODE_TYPE_MAP[n.data.typeId];
    if (!def) continue;
    for (const inp of def.inputs) {
      if (inp.required && !(incoming.get(n.id)?.has(inp.id))) {
        return { ok: false, problem: { nodeId: n.id, msg: `"${n.data.title}" requires input "${inp.label}"` } };
      }
    }
  }
  return { ok: true };
}

export async function runPipeline() {
  const store = useStore.getState();
  const tab = store.activeTab();
  const nodes = tab.nodes.filter(n => n.type !== "commentNode" && !n.data.disabled);
  const edges = tab.edges;

  const { order, error } = topoSort(nodes, edges);
  if (error) { toast.error(error); return; }
  const v = validate(nodes, edges);
  if (!v.ok && v.problem) {
    store.setRuntime(v.problem.nodeId, { status: "error", error: v.problem.msg });
    toast.error(v.problem.msg);
    return;
  }

  // --- Real Backend Execution via REST + WebSockets ---
  if (!isMockMode) {
    try {
      store.setRunning(true);
      // 1. Synchronize the current nodes and edges setup with database
      await store.savePipelineToServer();
      const pipelineId = useStore.getState().pipelineId;
      if (!pipelineId) throw new Error("Pipeline could not be synchronized with server.");

      // 2. Start the execution run on backend
      const { data: exec } = await api.startExecution(pipelineId);
      const execId = exec.id;
      
      // 3. Connect to live websocket execution logs stream
      const wsUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api')
        .replace(/^http/, 'ws') + `/executions/${execId}/stream`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "EXECUTION_STARTED") {
          nodes.forEach(n => store.setRuntime(n.id, { status: "running", error: undefined }));
        } else if (payload.type === "NODE_UPDATE") {
          const { nodeId, status, preview } = payload;
          store.setRuntime(nodeId, {
            status: status as any,
            preview,
            error: status === "error" ? "Execution failed" : undefined
          });
        } else if (payload.type === "LOG") {
          console.log(`[Backend Log] ${payload.nodeId || 'global'}: ${payload.message}`);
        } else if (payload.type === "EXECUTION_COMPLETED") {
          store.setRunning(false);
          toast.success("Pipeline ran successfully on backend.");
          ws.close();
        } else if (payload.type === "EXECUTION_FAILED") {
          store.setRunning(false);
          toast.error("Pipeline run failed on backend", { description: payload.error });
          ws.close();
        }
      };

      ws.onerror = (err) => {
        console.error("Execution WebSocket error:", err);
        store.setRunning(false);
        toast.error("Execution stream disconnected.");
      };
      
      return;
    } catch (err: any) {
      store.setRunning(false);
      toast.error("Failed to execute pipeline on backend", { description: err.message });
      return;
    }
  }

  store.setRunning(true);

  // Determine which nodes to actually re-run: any that are not "success"/"cached", plus their downstream
  const outgoing = new Map<string, string[]>();
  for (const e of edges) {
    const arr = outgoing.get(e.source) || []; arr.push(e.target); outgoing.set(e.source, arr);
  }
  const needsRun = new Set<string>();
  for (const n of nodes) {
    if (n.data.runtime.status !== "success" && n.data.runtime.status !== "cached") needsRun.add(n.id);
  }
  // downstream propagation
  let changed = true;
  while (changed) {
    changed = false;
    for (const src of Array.from(needsRun)) {
      for (const t of outgoing.get(src) || []) if (!needsRun.has(t)) { needsRun.add(t); changed = true; }
    }
  }
  // Mark not-needed nodes as cached
  for (const n of nodes) {
    if (!needsRun.has(n.id)) store.setRuntime(n.id, { status: "cached" });
  }

  const startT = performance.now();
  let errorCount = 0;
  let ranCount = 0;

  for (const layer of order) {
    const inLayer = layer.filter(id => needsRun.has(id));
    if (!inLayer.length) continue;
    // set all running simultaneously
    inLayer.forEach(id => store.setRuntime(id, { status: "running", error: undefined }));
    await Promise.all(inLayer.map(async (id) => {
      const delay = MOCK_EXECUTION_MIN_DELAY_MS + Math.random() * (MOCK_EXECUTION_MAX_DELAY_MS - MOCK_EXECUTION_MIN_DELAY_MS);
      await new Promise(r => setTimeout(r, delay));
      // 5% error chance
      if (Math.random() < MOCK_ERROR_RATE) {
        const messages = ["Connection reset by peer", "Schema mismatch on column 'value'", "Timeout after 5000ms", "Unexpected null in required field"];
        const msg = messages[Math.floor(Math.random() * messages.length)];
        store.setRuntime(id, { status: "error", error: msg });
        errorCount++;
      } else {
        const node = useStore.getState().activeTab().nodes.find(n => n.id === id);
        if (!node) return;
        const def = NODE_TYPE_MAP[node.data.typeId];
        const preview = def?.mockOutput(node.data.params);
        store.setRuntime(id, { status: "success", preview, ranAt: Date.now(), error: undefined });
        ranCount++;
      }
    }));
  }

  const totalMs = Math.round(performance.now() - startT);
  store.setRunning(false);
  if (errorCount > 0) {
    toast.error(`Pipeline finished with ${errorCount} error${errorCount > 1 ? "s" : ""}`, {
      description: `${ranCount} succeeded • ${totalMs}ms`,
    });
  } else {
    toast.success(`Pipeline ran successfully`, {
      description: `${ranCount} node${ranCount === 1 ? "" : "s"} in ${totalMs}ms`,
    });
  }
}
