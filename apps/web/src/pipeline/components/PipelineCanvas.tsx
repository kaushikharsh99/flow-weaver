import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background, BackgroundVariant, Controls, MiniMap, ReactFlowProvider,
  useReactFlow, type Connection, type Edge, type OnSelectionChangeParams, type ReactFlowInstance,
} from "reactflow";
import "reactflow/dist/style.css";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Focus } from "lucide-react";
import { useStore, type PipelineNode } from "../store";
import { NODE_TYPE_MAP, typesCompatible } from "../nodeTypes";
import { PipelineNodeView, CommentNodeView } from "./NodeViews";
import { NodeContextMenu, CanvasContextMenu } from "./ContextMenus";

const nodeTypes = { pipelineNode: PipelineNodeView, commentNode: CommentNodeView };

function InnerCanvas() {
  const tab = useStore(s => s.tabs.find(t => t.id === s.activeTabId)!);
  const onNodesChange = useStore(s => s.onNodesChange);
  const onEdgesChange = useStore(s => s.onEdgesChange);
  const onConnect = useStore(s => s.onConnect);
  const setSelected = useStore(s => s.setSelected);
  const addNode = useStore(s => s.addNode);
  const snapOn = useStore(s => s.ui.snapToGrid);

  const rf = useReactFlow();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [nodeMenu, setNodeMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null);
  const [canvasMenu, setCanvasMenu] = useState<{ x: number; y: number; flow: { x: number; y: number } } | null>(null);

  // Compute enriched edges with running/success styling
  const nodesById = useMemo(() => new Map(tab.nodes.map(n => [n.id, n])), [tab.nodes]);
  const edges: Edge[] = useMemo(() => tab.edges.map(e => {
    const src = nodesById.get(e.source);
    const status = src?.data.runtime.status;
    const running = status === "running";
    const done = status === "success" || status === "cached";
    return {
      ...e,
      type: "smoothstep",
      animated: running,
      style: {
        stroke: running ? "var(--accent-primary)" : done ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.18)",
        strokeWidth: 2,
        filter: running ? "drop-shadow(0 0 6px var(--accent-primary))" : undefined,
      },
    };
  }), [tab.edges, nodesById]);

  const isValidConnection = useCallback((c: Connection) => {
    const src = tab.nodes.find(n => n.id === c.source);
    const tgt = tab.nodes.find(n => n.id === c.target);
    if (!src || !tgt) return false;
    if (src.id === tgt.id) return false;
    const srcDef = NODE_TYPE_MAP[src.data.typeId];
    const tgtDef = NODE_TYPE_MAP[tgt.data.typeId];
    if (!srcDef || !tgtDef) return false;
    const outPort = srcDef.outputs.find(p => p.id === c.sourceHandle) || srcDef.outputs[0];
    const inPort = tgtDef.inputs.find(p => p.id === c.targetHandle) || tgtDef.inputs[0];
    return typesCompatible(outPort?.type, inPort?.type);
  }, [tab.nodes]);

  const handleConnect = useCallback((c: Connection) => {
    if (!isValidConnection(c)) { toast.error("Incompatible port types"); return; }
    onConnect(c);
  }, [isValidConnection, onConnect]);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.dataTransfer.dropEffect = "copy";
  }, []);
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const typeId = e.dataTransfer.getData("application/x-node-type");
    if (!typeId || !rfInstance) return;
    const bounds = wrapperRef.current!.getBoundingClientRect();
    const pos = rfInstance.screenToFlowPosition({ x: e.clientX - bounds.left, y: e.clientY - bounds.top });
    addNode(typeId, pos);
  }, [rfInstance, addNode]);

  const handleSelection = useCallback((p: OnSelectionChangeParams) => {
    setSelected(p.nodes.map(n => n.id));
  }, [setSelected]);

  const onNodeContextMenu = useCallback((e: React.MouseEvent, node: any) => {
    e.preventDefault();
    setSelected([node.id]);
    setNodeMenu({ x: e.clientX, y: e.clientY, nodeId: node.id });
    setCanvasMenu(null);
  }, [setSelected]);

  const onPaneContextMenu = useCallback((e: React.MouseEvent | MouseEvent) => {
    e.preventDefault();
    const ev = e as React.MouseEvent;
    if (!rfInstance || !wrapperRef.current) return;
    const bounds = wrapperRef.current.getBoundingClientRect();
    const flow = rfInstance.screenToFlowPosition({ x: ev.clientX - bounds.left, y: ev.clientY - bounds.top });
    setCanvasMenu({ x: ev.clientX, y: ev.clientY, flow });
    setNodeMenu(null);
  }, [rfInstance]);

  // dismiss menus on click
  useEffect(() => {
    const handler = () => { setNodeMenu(null); setCanvasMenu(null); };
    window.addEventListener("click", handler);
    return () => window.removeEventListener("click", handler);
  }, []);

  return (
    <div ref={wrapperRef} className="relative flex-1 h-full" onDragOver={onDragOver} onDrop={onDrop}>
      {tab.nodes.length === 0 && (
        <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center text-center p-6 z-10 select-none">
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="max-w-sm bg-neutral-900/60 border border-white/5 p-8 rounded-2xl backdrop-blur-md shadow-2xl"
          >
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-accent-primary to-accent-primary/40 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-accent-primary/20">
              <Focus size={18} className="text-white" />
            </div>
            <h3 className="text-[13px] font-semibold text-white/90">Design your Preprocessing Pipeline</h3>
            <p className="mt-2 text-[12px] text-white/50 leading-relaxed">
              Drag nodes from the sidebar palette, or search and import one of our templates.
            </p>
            <div className="mt-4 flex items-center justify-center gap-1.5">
              <kbd className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] text-white/60">Ctrl</kbd>
              <span className="text-[10px] text-white/40">+</span>
              <kbd className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] text-white/60">K</kbd>
              <span className="text-[10px] text-white/40">to open command center</span>
            </div>
          </motion.div>
        </div>
      )}
      <ReactFlow
        nodes={tab.nodes as PipelineNode[]}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        isValidConnection={isValidConnection}
        onSelectionChange={handleSelection}
        onNodeContextMenu={onNodeContextMenu}
        onPaneContextMenu={onPaneContextMenu}
        onInit={setRfInstance}
        fitView
        snapToGrid={snapOn}
        snapGrid={[15, 15]}
        panOnScroll
        selectionOnDrag
        panOnDrag={[1, 2]}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: "smoothstep" }}
        connectionLineStyle={{ stroke: "var(--accent-primary)", strokeWidth: 2 }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color={snapOn ? "rgba(255,255,255,0.14)" : "rgba(255,255,255,0.07)"} />
        <MiniMap
          pannable zoomable
          maskColor="rgba(10,10,12,0.75)"
          style={{ background: "rgba(20,20,24,0.9)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }}
          nodeColor={(n) => {
            const def = NODE_TYPE_MAP[(n.data as any)?.typeId];
            return def?.color || "#666";
          }}
          nodeStrokeColor="rgba(255,255,255,0.2)"
        />
        <Controls
          showInteractive={false}
          style={{ background: "rgba(20,20,24,0.9)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, overflow: "hidden" }}
        />
      </ReactFlow>

      <motion.button
        whileTap={{ scale: 0.94 }}
        onClick={() => rf.fitView({ padding: 0.2, duration: 300 })}
        className="absolute bottom-3 left-[132px] p-2 rounded-lg bg-white/[0.06] border border-white/10 backdrop-blur-xl text-white/80 hover:bg-white/10"
        title="Fit view"
      >
        <Focus size={14} />
      </motion.button>

      {nodeMenu && <NodeContextMenu x={nodeMenu.x} y={nodeMenu.y} nodeId={nodeMenu.nodeId} onClose={() => setNodeMenu(null)} />}
      {canvasMenu && <CanvasContextMenu x={canvasMenu.x} y={canvasMenu.y} flowPos={canvasMenu.flow} onClose={() => setCanvasMenu(null)} />}
    </div>
  );
}

export function PipelineCanvas() {
  return (
    <ReactFlowProvider>
      <InnerCanvas />
    </ReactFlowProvider>
  );
}
