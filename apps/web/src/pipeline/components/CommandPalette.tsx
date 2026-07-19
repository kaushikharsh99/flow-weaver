import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Trash2, Sun, Moon, Grid3x3, Plus, Search, LayoutGrid } from "lucide-react";
import { NODE_TYPES } from "../nodeTypes";
import { useStore } from "../store";
import { runPipeline } from "../runner";
import { cn } from "@/lib/utils";
import { api } from "@/api";
import type { Template } from "@/api/types";
import { toast } from "sonner";

interface Action { id: string; label: string; hint?: string; icon: any; run: () => void; }

export function CommandPalette() {
  const open = useStore(s => s.ui.paletteOpen);
  const setOpen = useStore(s => s.setPaletteOpen);
  const addNode = useStore(s => s.addNode);
  const clearCanvas = useStore(s => s.clearCanvas);
  const theme = useStore(s => s.ui.theme);
  const setTheme = useStore(s => s.setTheme);
  const snap = useStore(s => s.ui.snapToGrid);
  const setSnap = useStore(s => s.setSnapToGrid);
  const addTab = useStore(s => s.addTab);
  const recents = useStore(s => s.ui.recentNodeTypeIds);
  const pushRecent = useStore(s => s.pushRecentNodeType);

  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const [templates, setTemplates] = useState<Template[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQ("");
      setIdx(0);
      setTimeout(() => inputRef.current?.focus(), 20);
      // Fetch dynamic templates seeded from backend
      api.listTemplates()
        .then(res => setTemplates(res.data || []))
        .catch(err => console.error("Failed to load templates:", err));
    }
  }, [open]);

  const actions: Action[] = useMemo(() => [
    { id: "run", label: "Run pipeline", icon: Play, run: () => { setOpen(false); runPipeline(); } },
    { id: "clear", label: "Clear canvas", icon: Trash2, run: () => { if (confirm("Clear all nodes?")) { clearCanvas(); setOpen(false); } } },
    { id: "theme", label: `Toggle theme (${theme === "dark" ? "→ light" : "→ dark"})`, icon: theme === "dark" ? Sun : Moon, run: () => { setTheme(theme === "dark" ? "light" : "dark"); setOpen(false); } },
    { id: "snap", label: `${snap ? "Disable" : "Enable"} snap to grid`, icon: Grid3x3, run: () => { setSnap(!snap); setOpen(false); } },
    { id: "newtab", label: "New pipeline tab", icon: Plus, run: () => { addTab(); setOpen(false); } },
  ], [theme, snap, setOpen, clearCanvas, setTheme, setSnap, addTab]);

  const nodeItems = useMemo(() => {
    const query = q.trim().toLowerCase();
    let list = NODE_TYPES.slice();
    if (!query && recents.length) {
      const map = new Map(list.map(n => [n.id, n]));
      const recentList = recents.map(id => map.get(id)!).filter(Boolean);
      const rest = list.filter(n => !recents.includes(n.id));
      list = [...recentList, ...rest];
    }
    if (query) list = list.filter(n => n.label.toLowerCase().includes(query) || n.category.toLowerCase().includes(query));
    return list.slice(0, 8);
  }, [q, recents]);

  const filteredTemplates = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return templates;
    return templates.filter(t => t.name.toLowerCase().includes(query) || t.description.toLowerCase().includes(query));
  }, [q, templates]);

  const filteredActions = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return actions;
    return actions.filter(a => a.label.toLowerCase().includes(query));
  }, [q, actions]);

  type Item = 
    | { kind: "node"; id: string; label: string; run: () => void; icon: any; hint?: string } 
    | { kind: "template"; id: string; label: string; run: () => void; icon: any; hint?: string } 
    | { kind: "action"; id: string; label: string; run: () => void; icon: any; hint?: string };

  const flat: Item[] = [
    ...nodeItems.map(n => ({ kind: "node" as const, id: n.id, label: n.label, icon: n.icon, hint: n.category, run: () => { addNode(n.id, { x: 400 + Math.random()*80, y: 260 + Math.random()*80 }); pushRecent(n.id); setOpen(false); } })),
    ...filteredTemplates.map(t => ({ 
      kind: "template" as const, 
      id: t.id, 
      label: t.name, 
      icon: LayoutGrid, 
      hint: "Template", 
      run: () => {
        if (t.pipelineData && confirm(`Apply template "${t.name}"? Current canvas nodes in this tab will be replaced.`)) {
          const store = useStore.getState();
          store.pushHistory();
          const nodes = t.pipelineData.nodes.map((n: any) => ({
            id: n.id,
            type: n.type || 'pipelineNode',
            position: n.position,
            data: {
              ...n.data,
              runtime: { status: 'idle' }
            }
          }));
          const edges = t.pipelineData.edges.map((e: any) => ({
            ...e,
            type: 'smoothstep'
          }));
          useStore.setState({
            tabs: store.tabs.map(tab => tab.id === store.activeTabId ? { ...tab, name: t.name, nodes, edges } : tab),
            pipelineId: null, // Clear to force new pipeline creation on run
            selectedIds: []
          });
          toast.success(`Template "${t.name}" applied successfully.`);
          setOpen(false);
        }
      }
    })),
    ...filteredActions.map(a => ({ kind: "action" as const, id: a.id, label: a.label, icon: a.icon, run: a.run })),
  ];

  useEffect(() => { setIdx(0); }, [q]);

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setIdx(i => Math.min(flat.length - 1, i + 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setIdx(i => Math.max(0, i - 1)); }
    if (e.key === "Enter") { e.preventDefault(); flat[idx]?.run(); }
    if (e.key === "Escape") { e.preventDefault(); setOpen(false); }
  };

  // Group headers in render
  let lastKind: string | null = null;

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={() => setOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, y: -12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="fixed left-1/2 top-[18%] z-50 w-[92vw] max-w-[560px] -translate-x-1/2 rounded-2xl border border-white/10 bg-neutral-900/80 backdrop-blur-xl shadow-2xl shadow-black/60 overflow-hidden"
          >
            <div className="flex items-center gap-2 px-3 py-2.5 border-b border-white/10">
              <Search size={14} className="text-white/40" />
              <input
                ref={inputRef} value={q} onChange={e => setQ(e.target.value)} onKeyDown={onKey}
                placeholder="Search nodes and actions…"
                className="flex-1 bg-transparent outline-none text-[13px] text-white/95 placeholder:text-white/40"
              />
              <kbd className="text-[10px] text-white/40 border border-white/10 rounded px-1.5 py-0.5">ESC</kbd>
            </div>
            <div className="max-h-[52vh] overflow-y-auto py-1">
              {flat.length === 0 && <div className="px-4 py-6 text-[12px] text-white/40 text-center">No matches</div>}
              {flat.map((item, i) => {
                const showHeader = item.kind !== lastKind;
                lastKind = item.kind;
                const Icon = item.icon;
                return (
                  <div key={item.kind + item.id}>
                    {showHeader && (
                      <div className="px-3 pt-2 pb-1 text-[10px] uppercase tracking-wider text-white/40">
                        {item.kind === "node" 
                          ? (q ? "Add Node" : "Recent & Nodes") 
                          : item.kind === "template" 
                            ? "Pipeline Templates" 
                            : "Actions"}
                      </div>
                    )}
                    <button
                      onClick={item.run}
                      onMouseEnter={() => setIdx(i)}
                      className={cn(
                        "w-full flex items-center gap-2.5 px-3 py-2 text-left text-[12px]",
                        idx === i ? "bg-accent-primary/15 text-white/95" : "text-white/75 hover:bg-white/5",
                      )}
                    >
                      <Icon size={13} className="text-white/60" />
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.hint && <span className="text-[10px] text-white/40">{item.hint}</span>}
                    </button>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
