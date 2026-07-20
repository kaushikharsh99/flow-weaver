import { useEffect, useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { X, Search, LayoutGrid, Check, ArrowRight, Play } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useStore } from "../store";
import { api } from "@/api";
import type { Template } from "@/api/types";

interface TemplateGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function TemplateGalleryModal({ isOpen, onClose }: TemplateGalleryModalProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const applyTemplate = useStore(s => s.applyTemplate);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      api.listTemplates()
        .then(res => {
          setTemplates(res.data || []);
        })
        .catch(err => {
          console.error("Failed to load templates:", err);
          toast.error("Failed to fetch templates from the server");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isOpen]);

  const filteredTemplates = useMemo(() => {
    if (!searchQuery.trim()) return templates;
    const query = searchQuery.toLowerCase().trim();
    return templates.filter(t => 
      t.name.toLowerCase().includes(query) || 
      t.description.toLowerCase().includes(query)
    );
  }, [templates, searchQuery]);

  const handleApply = (template: Template) => {
    if (confirm(`Apply template "${template.name}"? This will replace your current workspace.`)) {
      applyTemplate(template);
      toast.success(`Loaded template: ${template.name}`);
      onClose();
    }
  };

  // Helper to extract unique node typeIds to display as a list of operations/badges
  const getTemplateSteps = (template: Template): string[] => {
    const pData = template.pipelineData || (template as any).pipeline_data;
    if (!pData || !Array.isArray(pData.nodes)) return [];
    return pData.nodes.map((n: any) => String(n.data?.title || n.data?.typeId || n.id));
  };

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[999] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md">
          {/* Dimmed backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0"
            onClick={onClose}
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.98 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="relative w-full max-w-4xl h-[75vh] flex flex-col rounded-xl bg-zinc-950 border border-zinc-800 shadow-2xl overflow-hidden z-10"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/50 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <LayoutGrid size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">
                    Template Gallery
                  </h3>
                  <p className="text-[11px] text-zinc-400">Start with a pre-configured data preprocessing pipeline</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="relative w-64">
                  <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search templates..."
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-3 py-1 text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-indigo-500/50"
                  />
                </div>

                <button
                  onClick={onClose}
                  className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Grid Content */}
            <div className="flex-1 overflow-y-auto p-6 bg-zinc-950/20">
              {loading ? (
                <div className="h-full w-full flex items-center justify-center text-zinc-400 text-xs">
                  Loading templates...
                </div>
              ) : filteredTemplates.length === 0 ? (
                <div className="h-full w-full flex flex-col items-center justify-center text-zinc-500 py-12">
                  <LayoutGrid size={32} className="mb-2 opacity-30" />
                  <span className="text-xs">No templates found</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredTemplates.map(t => {
                    const steps = getTemplateSteps(t);
                    return (
                      <div
                        key={t.id}
                        onClick={() => handleApply(t)}
                        className="group relative flex flex-col justify-between p-5 rounded-xl border border-zinc-800 hover:border-zinc-700 bg-zinc-900/30 hover:bg-zinc-900/60 cursor-pointer transition-all duration-200"
                      >
                        <div>
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="text-xs font-semibold text-zinc-100 group-hover:text-indigo-400 transition-colors">
                              {t.name}
                            </h4>
                            <span className="text-[9px] px-2 py-0.5 rounded bg-zinc-800/80 border border-zinc-700/50 text-zinc-400 uppercase tracking-wider font-semibold">
                              Built-in
                            </span>
                          </div>
                          
                          <p className="text-[11px] text-zinc-400 leading-relaxed mb-4">
                            {t.description}
                          </p>

                          {steps.length > 0 && (
                            <div className="mb-4">
                              <span className="text-[10px] text-zinc-500 font-medium block mb-1.5">Pipeline Steps:</span>
                              <div className="flex flex-wrap items-center gap-1.5">
                                {steps.map((step, idx) => (
                                  <div key={idx} className="flex items-center">
                                    <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300">
                                      {step}
                                    </span>
                                    {idx < steps.length - 1 && (
                                      <ArrowRight size={10} className="text-zinc-600 mx-1 flex-shrink-0" />
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center justify-end pt-3 border-t border-zinc-800/50">
                          <button className="flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                            <span>Use Template</span>
                            <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-zinc-800 bg-zinc-900/50 flex items-center justify-between text-[11px] text-zinc-500 flex-shrink-0">
              <span>Select any template to populate the canvas workspace.</span>
              <span>{filteredTemplates.length} templates available</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
}
