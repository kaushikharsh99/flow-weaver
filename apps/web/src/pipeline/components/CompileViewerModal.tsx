import { useState } from "react";
import { X, Copy, Download, Code2, Check, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

interface CompileViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  script: string;
  pipelineName: string;
}


export function CompileViewerModal({ isOpen, onClose, script, pipelineName }: CompileViewerModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(script);
    setCopied(true);
    toast.success("Compiled Python script copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([script], { type: "text/x-python" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${pipelineName.replace(/\s+/g, "_").toLowerCase()}_pipeline.py`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast.success("Downloaded pipeline.py!");
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full max-w-4xl max-h-[85vh] flex flex-col rounded-2xl bg-zinc-900 border border-white/10 shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.03]">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <Code2 size={18} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
                  Compiled Python Script <span className="text-xs font-normal text-purple-400 px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20">pipeline.py</span>
                </h3>
                <p className="text-xs text-white/50">Production-ready standalone Python code compiled from your visual DAG</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-white/80 font-medium transition-colors"
              >
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy Code"}
              </button>

              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs text-white font-medium transition-colors shadow-lg shadow-purple-500/20"
              >
                <Download size={14} />
                Download .py
              </button>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-colors ml-2"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Code Viewer Body */}
          <div className="flex-1 overflow-auto p-6 bg-zinc-950 font-mono text-sm leading-relaxed text-zinc-200 selection:bg-purple-500/30">
            <pre className="whitespace-pre-wrap font-mono text-xs text-purple-200/90">
              <code>{script}</code>
            </pre>
          </div>

          {/* Footer Info */}
          <div className="px-6 py-3 border-t border-white/10 bg-white/[0.02] flex items-center justify-between text-xs text-white/40">
            <span className="flex items-center gap-1.5">
              <Sparkles size={13} className="text-purple-400" /> Standalone script — executable anywhere with Python 3.10+
            </span>
            <span>FlowWeaver Compiler 2.0</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
