import { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { motion } from "framer-motion";
import { ChevronDown, ChevronRight, AlertCircle, Ban } from "lucide-react";
import { NODE_TYPE_MAP, PORT_TYPE_COLOR, getIcon } from "../nodeTypes";
import { useStore, type PipelineNodeData } from "../store";
import { cn } from "@/lib/utils";

function StatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    idle: "bg-white/25",
    running: "bg-accent-primary shadow-[0_0_10px] shadow-accent-primary",
    success: "bg-emerald-400",
    error: "bg-red-400",
    stale: "bg-amber-400/70",
    cached: "bg-emerald-400/60",
  };
  return (
    <span className={cn("h-2 w-2 rounded-full", map[status] || map.idle, status === "running" && "animate-pulse")} />
  );
}

function PipelineNodeInner({ id, data, selected }: NodeProps<PipelineNodeData>) {
  const def = NODE_TYPE_MAP[data.typeId];
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(data.title);
  const updateTitle = useStore(s => s.updateNodeTitle);
  const setCollapsed = useStore(s => s.setNodeCollapsed);
  if (!def) return null;
  const Icon = getIcon(def.icon);
  const collapsed = !!data.collapsed;
  const status = data.runtime.status;

  return (
    <motion.div
      initial={{ scale: 0.94, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 26 }}
      className={cn(
        "relative rounded-xl border backdrop-blur-xl min-w-[220px] max-w-[280px]",
        "bg-white/[0.04] border-white/10 text-white/90 shadow-lg shadow-black/40",
        selected && "ring-2 ring-accent-primary/70 shadow-[0_0_24px] shadow-accent-primary/30 border-accent-primary/50",
        status === "running" && "ring-2 ring-accent-primary/50 shadow-[0_0_28px] shadow-accent-primary/40",
        status === "error" && "ring-2 ring-red-500/60",
        data.disabled && "opacity-50",
      )}
      style={data.colorLabel ? { boxShadow: `inset 3px 0 0 ${data.colorLabel}` } : undefined}
    >
      {/* header */}
      <div className="flex items-center gap-2 px-3 py-2">
        <button
          onClick={(e) => { e.stopPropagation(); setCollapsed(id, !collapsed); }}
          className="text-white/50 hover:text-white/90 -ml-1"
          aria-label="Toggle collapse"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
        </button>
        <span
          className="flex h-6 w-6 items-center justify-center rounded-md flex-shrink-0"
          style={{ backgroundColor: def.color + "33", color: def.color }}
        >
          <Icon size={14} />
        </span>
        {editing ? (
          <input
            autoFocus
            value={draftTitle}
            onChange={(e) => setDraftTitle(e.target.value)}
            onBlur={() => { updateTitle(id, draftTitle || def.label); setEditing(false); }}
            onKeyDown={(e) => { if (e.key === "Enter") { updateTitle(id, draftTitle || def.label); setEditing(false); } if (e.key === "Escape") { setDraftTitle(data.title); setEditing(false); }}}
            className="flex-1 min-w-0 bg-white/5 border border-white/10 rounded px-1.5 py-0.5 text-[13px] font-medium outline-none focus:border-accent-primary/60"
          />
        ) : (
          <div
            onDoubleClick={() => { setDraftTitle(data.title); setEditing(true); }}
            className="flex-1 min-w-0 truncate text-[13px] font-medium"
            title="Double-click to rename"
          >
            {data.title}
          </div>
        )}
        <div className="flex items-center gap-1.5">
          {data.runtime.status === "stale" && <span className="text-[10px] text-amber-400/80">stale</span>}
          {data.disabled && <Ban size={12} className="text-white/40" />}
          {data.runtime.error && <span title={data.runtime.error}><AlertCircle size={12} className="text-red-400" /></span>}
          <StatusDot status={status} />
        </div>
      </div>

      {!collapsed && (
        <div className="px-3 pb-2 text-[11px] text-white/50 line-clamp-2">{def.description}</div>
      )}

      {/* Ports */}
      {def.inputs.map((p, i) => {
        const total = def.inputs.length;
        const top = total === 1 ? 22 : 18 + i * 18;
        return (
          <Handle
            key={p.id}
            id={p.id}
            type="target"
            position={Position.Left}
            style={{
              top,
              background: PORT_TYPE_COLOR[p.type],
              width: 10, height: 10, border: "2px solid rgba(0,0,0,0.6)",
            }}
          >
            {total > 1 && !collapsed && (
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[9px] text-white/60 whitespace-nowrap pointer-events-none">
                {p.label}
              </span>
            )}
          </Handle>
        );
      })}
      {def.outputs.map((p, i) => {
        const total = def.outputs.length;
        const top = total === 1 ? 22 : 18 + i * 18;
        return (
          <Handle
            key={p.id}
            id={p.id}
            type="source"
            position={Position.Right}
            style={{
              top,
              background: PORT_TYPE_COLOR[p.type],
              width: 10, height: 10, border: "2px solid rgba(0,0,0,0.6)",
            }}
          >
            {total > 1 && !collapsed && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[9px] text-white/60 whitespace-nowrap pointer-events-none">
                {p.label}
              </span>
            )}
          </Handle>
        );
      })}
    </motion.div>
  );
}

export const PipelineNodeView = memo(PipelineNodeInner);

function CommentNodeInner({ id, data, selected }: NodeProps<PipelineNodeData>) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(data.comment || "");
  const update = useStore(s => s.updateCommentText);
  return (
    <div
      className={cn(
        "rounded-xl backdrop-blur-xl border p-3 text-[12px] leading-relaxed",
        "bg-amber-300/10 border-amber-300/20 text-amber-100/90",
        selected && "ring-2 ring-amber-300/60",
      )}
      style={{ width: data.width || 220, minHeight: data.height || 120 }}
      onDoubleClick={() => setEditing(true)}
    >
      {editing ? (
        <textarea
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={() => { update(id, text); setEditing(false); }}
          className="w-full h-full min-h-[80px] bg-transparent outline-none resize-none text-amber-50"
        />
      ) : (
        <div className="whitespace-pre-wrap">{data.comment || "Double-click to edit…"}</div>
      )}
    </div>
  );
}

export const CommentNodeView = memo(CommentNodeInner);
