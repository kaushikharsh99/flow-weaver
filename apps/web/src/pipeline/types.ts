import type { LucideIcon } from "lucide-react";

export type PortType = "tabular" | "text" | "image" | "audio" | "any";
export type Category = "Loaders" | "Filters" | "Transform" | "Dedup" | "NLP" | "Export";

export interface Port {
  id: string;
  label: string;
  type: PortType;
  required?: boolean;
}

export type ParamField =
  | { key: string; label: string; description?: string; type: "text"; default?: string; placeholder?: string }
  | { key: string; label: string; description?: string; type: "number"; default?: number; min?: number; max?: number; step?: number }
  | { key: string; label: string; description?: string; type: "select"; default?: string; options: { label: string; value: string }[] }
  | { key: string; label: string; description?: string; type: "boolean"; default?: boolean }
  | { key: string; label: string; description?: string; type: "slider"; default?: number; min: number; max: number; step?: number }
  | { key: string; label: string; description?: string; type: "textarea"; default?: string; placeholder?: string; rows?: number }
  | { key: string; label: string; description?: string; type: "color"; default?: string }
  | { key: string; label: string; description?: string; type: "file"; default?: string; accept?: string; placeholder?: string }
  | { key: string; label: string; description?: string; type: "regex"; default?: string; placeholder?: string }
  | { key: string; label: string; description?: string; type: "column"; default?: string; placeholder?: string }
  | { key: string; label: string; description?: string; type: "secret"; default?: string; placeholder?: string }
  | { key: string; label: string; description?: string; type: "json"; default?: string; placeholder?: string; rows?: number }
  | { key: string; label: string; description?: string; type: "expression"; default?: string; placeholder?: string };

export type MockPreview =
  | { kind: "table"; columns: string[]; rows: (string | number)[][]; note?: string; stats?: Record<string, string | number> }
  | { kind: "text"; snippets: string[]; stats?: Record<string, string | number>; badges?: string[] }
  | { kind: "file"; name: string; format: string; size: string; rows?: number; stats?: Record<string, string | number> }
  | { kind: "stat"; title: string; stats: Record<string, string | number>; note?: string };

export interface NodeTypeDef {
  id: string;
  label: string;
  category: Category;
  description: string;
  icon: LucideIcon;
  color: string; // hex, muted
  inputs: Port[];
  outputs: Port[];
  paramsSchema: ParamField[];
  mockOutput: (params: Record<string, any>, inputSample?: any) => MockPreview;
}

export type NodeStatus = "idle" | "running" | "success" | "error" | "stale" | "cached";

export interface NodeRuntime {
  status: NodeStatus;
  error?: string;
  preview?: MockPreview;
  ranAt?: number;
}
