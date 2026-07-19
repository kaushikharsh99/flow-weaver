import { useRef, useState } from "react";
import {
  Play, Square, Undo2, Redo2, Save, Upload, X, Plus, Sun, Moon, Command as CommandIcon, Grid3x3, Zap,
} from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useStore } from "../store";
import { runPipeline } from "../runner";
import { cn } from "@/lib/utils";

export function Toolbar() {
  const tabs = useStore(s => s.tabs);
  const activeId = useStore(s => s.activeTabId);
  const setActive = useStore(s => s.setActiveTab);
  const addTab = useStore(s => s.addTab);
  const closeTab = useStore(s => s.closeTab);
  const rename = useStore(s => s.renameActiveTab);
  const running = useStore(s => s.running);
  const setRunning = useStore(s => s.setRunning);
  const undo = useStore(s => s.undo);
  const redo = useStore(s => s.redo);
  const history = useStore(s => s.history);
  const future = useStore(s => s.future);
  const theme = useStore(s => s.ui.theme);
  const setTheme = useStore(s => s.setTheme);
  const snapOn = useStore(s => s.ui.snapToGrid);
  const setSnap = useStore(s => s.setSnapToGrid);
  const setPalette = useStore(s => s.setPaletteOpen);
  const exportJSON = useStore(s => s.exportJSON);
  const importJSON = useStore(s => s.importJSON);

  const activeTab = tabs.find(t => t.id === activeId)!;
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState(activeTab.name);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSave = () => {
    const json = exportJSON();
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${activeTab.name.replace(/\s+/g, "-").toLowerCase()}.pipeline.json`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    toast.success("Pipeline saved");
  };
  const handleLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      try { importJSON(String(reader.result)); toast.success("Pipeline loaded"); }
      catch { toast.error("Malformed pipeline file"); }
    };
    reader.readAsText(f);
    e.target.value = "";
  };
  const handleRun = async () => {
    if (running) { setRunning(false); toast("Run stopped"); return; }
    await runPipeline();
  };

  return (
    <div className="h-12 flex-shrink-0 flex items-center border-b border-white/10 bg-white/[0.03] backdrop-blur-xl px-3 gap-2">
      <div className="flex items-center gap-2 mr-2">
        <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-accent-primary to-accent-primary/40 flex items-center justify-center">
          <Zap size={14} className="text-white" />
        </div>
        <span className="text-[13px] font-semibold text-white/90 tracking-tight">FlowWeaver</span>
      </div>

      <div className="h-5 w-px bg-white/10 mx-1" />

      {/* pipeline name */}
      {editingName ? (
        <input
          autoFocus value={draftName}
          onChange={e => setDraftName(e.target.value)}
          onBlur={() => { rename(draftName || "Untitled"); setEditingName(false); }}
          onKeyDown={e => { if (e.key === "Enter") { rename(draftName || "Untitled"); setEditingName(false); } if (e.key === "Escape") { setDraftName(activeTab.name); setEditingName(false); } }}
          className="bg-white/5 border border-white/10 rounded px-2 py-1 text-[12px] outline-none focus:border-accent-primary/60 text-white/90"
        />
      ) : (
        <button
          onClick={() => { setDraftName(activeTab.name); setEditingName(true); }}
          className="text-[12px] font-medium text-white/85 hover:text-white/95 px-2 py-1 rounded hover:bg-white/5"
        >
          {activeTab.name}
        </button>
      )}

      {/* tabs */}
      <div className="flex items-center gap-1 ml-2 overflow-x-auto">
        {tabs.map(t => (
          <div
            key={t.id}
            onClick={() => setActive(t.id)}
            className={cn(
              "group flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 rounded-md text-[11px] cursor-pointer transition-colors",
              t.id === activeId ? "bg-white/8 text-white/95" : "text-white/50 hover:bg-white/5 hover:text-white/80",
            )}
          >
            <span className="max-w-[100px] truncate">{t.name}</span>
            {tabs.length > 1 && (
              <button
                onClick={(e) => { e.stopPropagation(); closeTab(t.id); }}
                className="opacity-0 group-hover:opacity-100 hover:bg-white/10 rounded p-0.5"
              >
                <X size={10} />
              </button>
            )}
          </div>
        ))}
        <button onClick={addTab} className="p-1 rounded hover:bg-white/5 text-white/50 hover:text-white/80" title="New pipeline">
          <Plus size={13} />
        </button>
      </div>

      <div className="flex-1" />

      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={() => setPalette(true)}
        className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[11px] text-white/60 hover:text-white/90"
      >
        <CommandIcon size={11} /> <span>K</span>
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={undo}
        disabled={!history.length}
        className="p-1.5 rounded hover:bg-white/5 text-white/70 disabled:opacity-30"
        title="Undo"
      >
        <Undo2 size={14} />
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={redo}
        disabled={!future.length}
        className="p-1.5 rounded hover:bg-white/5 text-white/70 disabled:opacity-30"
        title="Redo"
      >
        <Redo2 size={14} />
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => setSnap(!snapOn)}
        className={cn("p-1.5 rounded text-white/70 hover:bg-white/5", snapOn && "bg-accent-primary/20 text-accent-primary")}
        title="Snap to grid"
      >
        <Grid3x3 size={14} />
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={handleSave}
        className="p-1.5 rounded hover:bg-white/5 text-white/70"
        title="Save JSON"
      >
        <Save size={14} />
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => fileRef.current?.click()}
        className="p-1.5 rounded hover:bg-white/5 text-white/70"
        title="Load JSON"
      >
        <Upload size={14} />
      </motion.button>
      <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={handleLoad} />

      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        className="p-1.5 rounded hover:bg-white/5 text-white/70"
        title="Toggle theme"
      >
        {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.96 }}
        onClick={handleRun}
        className={cn(
          "ml-1 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium",
          running
            ? "bg-red-500/90 hover:bg-red-500 text-white"
            : "bg-accent-primary hover:bg-accent-primary/90 text-white shadow-[0_0_20px] shadow-accent-primary/40",
        )}
      >
        {running ? <><Square size={12} /> Stop</> : <><Play size={12} /> Run</>}
      </motion.button>
    </div>
  );
}
