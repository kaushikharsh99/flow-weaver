import { useEffect } from "react";
import { Toaster } from "sonner";
import { Sidebar } from "./Sidebar";
import { Inspector } from "./Inspector";
import { Toolbar } from "./Toolbar";
import { PipelineCanvas } from "./PipelineCanvas";
import { CommandPalette } from "./CommandPalette";
import { useStore } from "../store";

export function PipelineBuilder() {
  const theme = useStore(s => s.ui.theme);
  const setPalette = useStore(s => s.setPaletteOpen);
  const undo = useStore(s => s.undo);
  const redo = useStore(s => s.redo);
  const copySelection = useStore(s => s.copySelection);
  const paste = useStore(s => s.paste);
  const dup = useStore(s => s.duplicateSelection);
  const del = useStore(s => s.deleteSelection);
  const nudge = useStore(s => s.nudgeSelection);
  const selectAll = useStore(s => s.selectAll);
  const setInspectorOpen = useStore(s => s.setInspectorOpen);
  const setSelected = useStore(s => s.setSelected);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      const t = e.target as HTMLElement;
      const isText = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable || t.tagName === "SELECT");

      if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette(true); return; }
      if (isText) return;

      if (mod && e.shiftKey && e.key.toLowerCase() === "z") { e.preventDefault(); redo(); return; }
      if (mod && e.key.toLowerCase() === "z") { e.preventDefault(); undo(); return; }
      if (mod && e.key.toLowerCase() === "y") { e.preventDefault(); redo(); return; }
      if (mod && e.key.toLowerCase() === "c") { e.preventDefault(); copySelection(); return; }
      if (mod && e.key.toLowerCase() === "v") { e.preventDefault(); paste({ x: 40, y: 40 }); return; }
      if (mod && e.key.toLowerCase() === "d") { e.preventDefault(); dup(); return; }
      if (mod && e.key.toLowerCase() === "a") { e.preventDefault(); selectAll(); return; }
      if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); del(); return; }
      if (e.key === "Escape") { setSelected([]); setInspectorOpen(false); return; }
      const step = e.shiftKey ? 10 : 1;
      if (e.key === "ArrowLeft") { e.preventDefault(); nudge(-step, 0); }
      if (e.key === "ArrowRight") { e.preventDefault(); nudge(step, 0); }
      if (e.key === "ArrowUp") { e.preventDefault(); nudge(0, -step); }
      if (e.key === "ArrowDown") { e.preventDefault(); nudge(0, step); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [copySelection, del, dup, nudge, paste, redo, selectAll, setInspectorOpen, setPalette, setSelected, undo]);

  return (
    <div className={`h-screen w-screen flex flex-col overflow-hidden ${theme === "dark" ? "theme-dark" : "theme-light"}`}>
      <Toolbar />
      <div className="flex-1 flex min-h-0">
        <Sidebar />
        <PipelineCanvas />
        <Inspector />
      </div>
      <CommandPalette />
      <Toaster theme={theme === "dark" ? "dark" : "light"} position="bottom-right" />
    </div>
  );
}
