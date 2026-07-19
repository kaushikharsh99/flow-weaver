import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sliders, Eye, StickyNote, AlertTriangle } from "lucide-react";
import { NODE_TYPE_MAP } from "../nodeTypes";
import { useStore } from "../store";
import type { MockPreview, ParamField } from "../types";
import { cn } from "@/lib/utils";

function Field({ f, value, onChange }: { f: ParamField; value: any; onChange: (v: any) => void }) {
  const label = (
    <label className="text-[11px] uppercase tracking-wide text-white/50 font-medium">{f.label}</label>
  );
  if (f.type === "text") {
    return (
      <div className="space-y-1">
        {label}
        <input
          value={value ?? ""} onChange={e => onChange(e.target.value)} placeholder={f.placeholder}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-[12px] outline-none focus:border-accent-primary/60 text-white/90"
        />
      </div>
    );
  }
  if (f.type === "number") {
    return (
      <div className="space-y-1">
        {label}
        <input
          type="number" value={value ?? ""} min={f.min} max={f.max} step={f.step}
          onChange={e => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-[12px] outline-none focus:border-accent-primary/60 text-white/90"
        />
      </div>
    );
  }
  if (f.type === "select") {
    return (
      <div className="space-y-1">
        {label}
        <select
          value={value ?? ""} onChange={e => onChange(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-[12px] outline-none focus:border-accent-primary/60 text-white/90"
        >
          {f.options.map(o => <option key={o.value} value={o.value} className="bg-neutral-900">{o.label}</option>)}
        </select>
      </div>
    );
  }
  if (f.type === "boolean") {
    return (
      <div className="flex items-center justify-between py-1">
        <span className="text-[12px] text-white/80">{f.label}</span>
        <button
          onClick={() => onChange(!value)}
          className={cn(
            "relative h-5 w-9 rounded-full transition-colors",
            value ? "bg-accent-primary" : "bg-white/15",
          )}
        >
          <span className={cn("absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform", value && "translate-x-4")} />
        </button>
      </div>
    );
  }
  if (f.type === "slider") {
    return (
      <div className="space-y-1">
        <div className="flex justify-between">
          {label}
          <span className="text-[11px] text-white/60 tabular-nums">{value ?? f.default}</span>
        </div>
        <input
          type="range" min={f.min} max={f.max} step={f.step ?? 1} value={value ?? f.default ?? f.min}
          onChange={e => onChange(Number(e.target.value))}
          className="w-full accent-[color:var(--accent-primary)]"
        />
      </div>
    );
  }
  return null;
}

function PreviewRender({ p }: { p: MockPreview }) {
  if (p.kind === "table") {
    return (
      <div className="space-y-3">
        {p.stats && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(p.stats).map(([k, v]) => (
              <div key={k} className="px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[11px]">
                <span className="text-white/50">{k}</span> <span className="text-white/90 tabular-nums">{v}</span>
              </div>
            ))}
          </div>
        )}
        <div className="overflow-auto max-h-[360px] rounded-lg border border-white/10">
          <table className="w-full text-[11px]">
            <thead className="bg-white/5 sticky top-0">
              <tr>{p.columns.map(c => <th key={c} className="text-left px-2 py-1.5 font-medium text-white/70 whitespace-nowrap">{c}</th>)}</tr>
            </thead>
            <tbody>
              {p.rows.map((r, i) => (
                <tr key={i} className="border-t border-white/5 hover:bg-white/[0.03]">
                  {r.map((v, j) => <td key={j} className="px-2 py-1.5 text-white/80 tabular-nums whitespace-nowrap">{String(v)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  if (p.kind === "text") {
    return (
      <div className="space-y-3">
        {p.badges && (
          <div className="flex flex-wrap gap-1.5">
            {p.badges.map((b, i) => <span key={i} className="px-2 py-0.5 rounded-full bg-accent-primary/15 border border-accent-primary/30 text-[10px] text-accent-primary">{b}</span>)}
          </div>
        )}
        <div className="space-y-2">
          {p.snippets.map((s, i) => (
            <div key={i} className="rounded-lg bg-white/5 border border-white/10 p-2.5 text-[12px] text-white/80 leading-relaxed">{s}</div>
          ))}
        </div>
        {p.stats && (
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(p.stats).map(([k, v]) => (
              <div key={k} className="px-2 py-1.5 rounded-md bg-white/[0.03] border border-white/10">
                <div className="text-[10px] text-white/50">{k}</div>
                <div className="text-[12px] text-white/90 tabular-nums">{v}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
  if (p.kind === "file") {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
          <div className="text-[11px] text-white/50">Output file</div>
          <div className="text-[13px] font-medium text-white/90 mt-0.5 break-all">{p.name}</div>
          <div className="mt-2 flex gap-2 text-[11px]">
            <span className="px-2 py-0.5 rounded bg-white/5">{p.format}</span>
            <span className="px-2 py-0.5 rounded bg-white/5">{p.size}</span>
            {p.rows !== undefined && <span className="px-2 py-0.5 rounded bg-white/5">{p.rows.toLocaleString()} rows</span>}
          </div>
        </div>
        {p.stats && (
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(p.stats).map(([k, v]) => (
              <div key={k} className="px-2 py-1.5 rounded-md bg-white/[0.03] border border-white/10">
                <div className="text-[10px] text-white/50">{k}</div>
                <div className="text-[12px] text-white/90 tabular-nums">{v}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
  if (p.kind === "stat") {
    return (
      <div className="space-y-3">
        <div className="text-[13px] font-medium text-white/90">{p.title}</div>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(p.stats).map(([k, v]) => (
            <div key={k} className="px-2.5 py-2 rounded-lg bg-white/[0.03] border border-white/10">
              <div className="text-[10px] text-white/50">{k}</div>
              <div className="text-[12px] text-white/90 tabular-nums break-all">{v}</div>
            </div>
          ))}
        </div>
        {p.note && <div className="text-[11px] text-white/50">{p.note}</div>}
      </div>
    );
  }
  return null;
}

export function Inspector() {
  const open = useStore(s => s.ui.inspectorOpen);
  const setOpen = useStore(s => s.setInspectorOpen);
  const selectedIds = useStore(s => s.selectedIds);
  const tab = useStore(s => s.tabs.find(t => t.id === s.activeTabId)!);
  const updateParams = useStore(s => s.updateNodeParams);
  const [activeTab, setActiveTab] = useState<"params" | "preview" | "notes">("params");

  const node = useMemo(() => {
    if (selectedIds.length !== 1) return null;
    return tab.nodes.find(n => n.id === selectedIds[0]) || null;
  }, [selectedIds, tab.nodes]);

  const def = node ? NODE_TYPE_MAP[node.data.typeId] : null;
  const show = open && node && def;

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ x: 320, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 320, opacity: 0 }}
          transition={{ type: "spring", stiffness: 320, damping: 30 }}
          className="w-[340px] flex-shrink-0 border-l border-white/10 bg-white/[0.03] backdrop-blur-xl flex flex-col"
        >
          <div className="flex items-center gap-2 px-3 py-2.5 border-b border-white/10">
            <span
              className="flex h-6 w-6 items-center justify-center rounded-md"
              style={{ backgroundColor: def!.color + "33", color: def!.color }}
            >
              <def.icon size={13} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-[12px] font-medium truncate text-white/90">{node!.data.title}</div>
              <div className="text-[10px] uppercase tracking-wide text-white/40">{def!.category}</div>
            </div>
            <button onClick={() => setOpen(false)} className="p-1 rounded hover:bg-white/5 text-white/60">
              <X size={14} />
            </button>
          </div>

          {node!.data.runtime.status === "stale" && (
            <div className="mx-3 mt-2 flex items-center gap-2 rounded-md border border-amber-400/30 bg-amber-400/10 px-2 py-1.5 text-[11px] text-amber-200">
              <AlertTriangle size={12} /> Parameters changed — re-run pipeline
            </div>
          )}
          {node!.data.runtime.error && (
            <div className="mx-3 mt-2 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1.5 text-[11px] text-red-200">
              {node!.data.runtime.error}
            </div>
          )}

          <div className="flex border-b border-white/10 text-[12px]">
            {([["params", "Parameters", Sliders], ["preview", "Preview", Eye], ["notes", "Notes", StickyNote]] as const).map(([id, label, Icon]) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 py-2 relative text-white/60 hover:text-white/90 transition-colors",
                  activeTab === id && "text-white/95",
                )}
              >
                <Icon size={12} /> {label}
                {activeTab === id && (
                  <motion.span layoutId="inspector-underline" className="absolute bottom-0 left-3 right-3 h-[2px] bg-accent-primary rounded-full" />
                )}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {activeTab === "params" && (
              <>
                {def!.paramsSchema.length === 0 && <div className="text-[12px] text-white/40">No parameters.</div>}
                {def!.paramsSchema.map(f => (
                  <Field
                    key={f.key} f={f}
                    value={node!.data.params[f.key]}
                    onChange={(v) => updateParams(node!.id, { [f.key]: v })}
                  />
                ))}
              </>
            )}
            {activeTab === "preview" && (
              <>
                {node!.data.runtime.preview
                  ? <PreviewRender p={node!.data.runtime.preview} />
                  : (
                    <div className="rounded-lg border border-dashed border-white/10 p-6 text-center text-[12px] text-white/40">
                      Run the pipeline to see output for this node.
                    </div>
                  )}
              </>
            )}
            {activeTab === "notes" && (
              <textarea
                placeholder="Notes about this node…"
                defaultValue={node!.data.comment || ""}
                onBlur={(e) => useStore.getState().updateCommentText(node!.id, e.target.value)}
                className="w-full min-h-[240px] bg-white/5 border border-white/10 rounded-lg p-2.5 text-[12px] outline-none focus:border-accent-primary/60 text-white/90 resize-none"
              />
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
