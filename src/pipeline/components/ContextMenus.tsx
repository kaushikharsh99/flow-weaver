import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Pencil, Copy, Ban, Trash2, StickyNote, Plus, ClipboardPaste, MousePointer, Palette, Play,
} from "lucide-react";
import { useStore } from "../store";
import { NODE_TYPES } from "../nodeTypes";
import { cn } from "@/lib/utils";
import { runPipeline } from "../runner";

const LABEL_COLORS = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#a855f7", "#ec4899"];

function MenuShell({ x, y, children }: { x: number; y: number; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: -4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.12 }}
      style={{ left: x, top: y }}
      className="fixed z-50 min-w-[200px] rounded-xl border border-white/10 bg-neutral-900/90 backdrop-blur-xl shadow-2xl shadow-black/60 py-1 text-[12px] text-white/90"
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => e.preventDefault()}
    >
      {children}
    </motion.div>
  );
}

function MenuItem({ icon: Icon, label, onClick, danger, disabled }: any) {
  return (
    <button
      onClick={onClick} disabled={disabled}
      className={cn(
        "w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-white/5",
        danger && "text-red-300 hover:bg-red-500/10", disabled && "opacity-40 cursor-not-allowed",
      )}
    >
      {Icon && <Icon size={13} className="text-white/60" />}
      <span>{label}</span>
    </button>
  );
}

export function NodeContextMenu({ x, y, nodeId, onClose }: { x: number; y: number; nodeId: string; onClose: () => void }) {
  const node = useStore(s => s.tabs.find(t => t.id === s.activeTabId)!.nodes.find(n => n.id === nodeId));
  const duplicate = useStore(s => s.duplicateSelection);
  const del = useStore(s => s.deleteSelection);
  const setDisabled = useStore(s => s.setNodeDisabled);
  const setColorLabel = useStore(s => s.setNodeColorLabel);
  const addComment = useStore(s => s.addCommentNode);
  const setInspector = useStore(s => s.setInspectorOpen);
  const [showColors, setShowColors] = useState(false);
  if (!node) return null;

  return (
    <MenuShell x={x} y={y}>
      <MenuItem icon={Pencil} label="Rename (double-click title)" onClick={() => { setInspector(true); onClose(); }} />
      <MenuItem icon={Copy} label="Duplicate" onClick={() => { duplicate(); onClose(); }} />
      <div className="relative">
        <button
          onClick={() => setShowColors(v => !v)}
          className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-white/5"
        >
          <Palette size={13} className="text-white/60" />
          <span>Color label</span>
          <div className="ml-auto flex items-center gap-1">
            {node.data.colorLabel && <span className="h-2.5 w-2.5 rounded-full" style={{ background: node.data.colorLabel }} />}
            <span className="text-white/40">›</span>
          </div>
        </button>
        {showColors && (
          <div className="px-3 py-2 border-t border-white/5 flex flex-wrap gap-1.5">
            <button
              onClick={() => { setColorLabel(nodeId, undefined); onClose(); }}
              className="h-5 w-5 rounded-full border border-white/20 bg-transparent flex items-center justify-center text-white/60 text-[9px]"
            >×</button>
            {LABEL_COLORS.map(c => (
              <button key={c} onClick={() => { setColorLabel(nodeId, c); onClose(); }}
                className="h-5 w-5 rounded-full border border-white/10 hover:scale-110 transition-transform"
                style={{ background: c }} />
            ))}
          </div>
        )}
      </div>
      <MenuItem icon={Ban} label={node.data.disabled ? "Enable" : "Disable"} onClick={() => { setDisabled(nodeId, !node.data.disabled); onClose(); }} />
      <MenuItem icon={StickyNote} label="Add comment nearby" onClick={() => { addComment({ x: node.position.x + 260, y: node.position.y }); onClose(); }} />
      <div className="h-px bg-white/5 my-1" />
      <MenuItem icon={Trash2} label="Delete" danger onClick={() => { del(); onClose(); }} />
    </MenuShell>
  );
}

export function CanvasContextMenu({ x, y, flowPos, onClose }: { x: number; y: number; flowPos: { x: number; y: number }; onClose: () => void }) {
  const addNode = useStore(s => s.addNode);
  const paste = useStore(s => s.paste);
  const selectAll = useStore(s => s.selectAll);
  const clearCanvas = useStore(s => s.clearCanvas);
  const [showAdd, setShowAdd] = useState(false);
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const query = q.toLowerCase();
    return NODE_TYPES.filter(n => !query || n.label.toLowerCase().includes(query)).slice(0, 6);
  }, [q]);

  return (
    <MenuShell x={x} y={y}>
      {!showAdd ? (
        <>
          <MenuItem icon={Plus} label="Add node here…" onClick={() => setShowAdd(true)} />
          <MenuItem icon={ClipboardPaste} label="Paste" onClick={() => { paste({ x: 0, y: 0 }); onClose(); }} />
          <MenuItem icon={MousePointer} label="Select all" onClick={() => { selectAll(); onClose(); }} />
          <MenuItem icon={Play} label="Run pipeline" onClick={() => { runPipeline(); onClose(); }} />
          <div className="h-px bg-white/5 my-1" />
          <MenuItem icon={Trash2} label="Clear canvas" danger onClick={() => { if (confirm("Clear all nodes?")) { clearCanvas(); onClose(); } }} />
        </>
      ) : (
        <div className="w-[240px]">
          <div className="px-2 pt-2">
            <input
              autoFocus value={q} onChange={e => setQ(e.target.value)}
              placeholder="Search nodes…"
              className="w-full bg-white/5 border border-white/10 rounded px-2 py-1 text-[12px] outline-none focus:border-accent-primary/60"
            />
          </div>
          <div className="mt-1 max-h-[240px] overflow-y-auto py-1">
            {filtered.map(n => {
              const Icon = n.icon;
              return (
                <button
                  key={n.id}
                  onClick={() => { addNode(n.id, flowPos); onClose(); }}
                  className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-white/5 text-left"
                >
                  <span className="flex h-5 w-5 items-center justify-center rounded" style={{ background: n.color + "22", color: n.color }}>
                    <Icon size={11} />
                  </span>
                  <span className="text-[12px] truncate">{n.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </MenuShell>
  );
}
