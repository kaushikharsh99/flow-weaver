import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight, Search, PanelLeftClose, PanelLeftOpen, StickyNote } from "lucide-react";
import { CATEGORIES, NODE_TYPES, getIcon } from "../nodeTypes";
import { useStore } from "../store";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const width = useStore(s => s.ui.sidebarWidth);
  const collapsed = useStore(s => s.ui.sidebarCollapsed);
  const setWidth = useStore(s => s.setSidebarWidth);
  const toggle = useStore(s => s.toggleSidebar);
  const addNode = useStore(s => s.addNode);
  const addComment = useStore(s => s.addCommentNode);

  const [query, setQuery] = useState("");
  const [openCats, setOpenCats] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(CATEGORIES.map(c => [c, true])),
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return NODE_TYPES.filter(n =>
      !q || n.label.toLowerCase().includes(q) || n.category.toLowerCase().includes(q) || n.description.toLowerCase().includes(q),
    );
  }, [query]);

  const grouped = useMemo(() => {
    const m: Record<string, typeof NODE_TYPES> = {};
    for (const n of filtered) (m[n.category] ||= []).push(n);
    return m;
  }, [filtered]);

  const onDragStart = (e: React.DragEvent, typeId: string) => {
    e.dataTransfer.setData("application/x-node-type", typeId);
    e.dataTransfer.effectAllowed = "copy";
  };

  const onClickAdd = (typeId: string) => {
    // add near canvas center - simple heuristic
    addNode(typeId, { x: 280 + Math.random() * 100, y: 200 + Math.random() * 100 });
  };

  if (collapsed) {
    return (
      <div className="w-14 flex-shrink-0 border-r border-white/10 bg-white/[0.03] backdrop-blur-xl flex flex-col items-center py-3 gap-2">
        <button onClick={toggle} className="p-2 rounded-lg hover:bg-white/5 text-white/70" title="Expand sidebar">
          <PanelLeftOpen size={16} />
        </button>
        <div className="flex-1 flex flex-col gap-1 overflow-y-auto py-2">
          {CATEGORIES.map(cat => {
            const first = NODE_TYPES.find(n => n.category === cat);
            if (!first) return null;
            const Icon = getIcon(first.icon);
            return (
              <button key={cat} title={cat} className="p-2 rounded-lg hover:bg-white/5"
                style={{ color: first.color }}>
                <Icon size={16} />
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative flex-shrink-0 border-r border-white/10 bg-white/[0.03] backdrop-blur-xl flex flex-col"
      style={{ width }}
    >
      <div className="flex items-center gap-2 p-3 border-b border-white/10">
        <div className="flex-1 relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/40" />
          <input
            value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search nodes…"
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-7 pr-2 py-1.5 text-[12px] outline-none focus:border-accent-primary/60 text-white/90 placeholder:text-white/40"
          />
        </div>
        <button onClick={toggle} className="p-1.5 rounded-lg hover:bg-white/5 text-white/60" title="Collapse">
          <PanelLeftClose size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {CATEGORIES.map(cat => {
          const items = grouped[cat] || [];
          if (!items.length) return null;
          const open = openCats[cat];
          const catColor = items[0]?.color || "#666";
          return (
            <div key={cat}>
              <button
                onClick={() => setOpenCats(s => ({ ...s, [cat]: !s[cat] }))}
                className="w-full flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-white/5 text-white/70 group"
              >
                {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: catColor }}>{cat}</span>
                <span className="ml-auto text-[10px] text-white/40">{items.length}</span>
              </button>
              <AnimatePresence initial={false}>
                {open && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="overflow-hidden"
                  >
                    <div className="pl-2 py-0.5 space-y-0.5">
                      {items.map(n => {
                        const Icon = getIcon(n.icon);
                        return (
                          <div
                            key={n.id}
                            draggable
                            onDragStart={(e) => onDragStart(e, n.id)}
                            onClick={() => onClickAdd(n.id)}
                            className={cn(
                              "group flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-grab active:cursor-grabbing",
                              "hover:bg-white/5 border border-transparent hover:border-white/10 transition-colors",
                            )}
                          >
                            <span className="flex h-6 w-6 items-center justify-center rounded-md flex-shrink-0"
                              style={{ backgroundColor: n.color + "22", color: n.color }}>
                              <Icon size={13} />
                            </span>
                            <div className="min-w-0 flex-1">
                              <div className="text-[12px] text-white/85 truncate">{n.label}</div>
                              <div className="text-[10px] text-white/40 truncate">{n.description}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}

        <div className="pt-2 mt-2 border-t border-white/5">
          <button
            onClick={() => addComment({ x: 300, y: 300 })}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 text-white/70"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-300/20 text-amber-300">
              <StickyNote size={13} />
            </span>
            <span className="text-[12px]">Add sticky note</span>
          </button>
        </div>
      </div>

      {/* resize handle */}
      <div
        onMouseDown={(e) => {
          e.preventDefault();
          const startX = e.clientX;
          const startW = width;
          const move = (ev: MouseEvent) => setWidth(startW + ev.clientX - startX);
          const up = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
          window.addEventListener("mousemove", move); window.addEventListener("mouseup", up);
        }}
        className="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-accent-primary/40"
      />
    </div>
  );
}
