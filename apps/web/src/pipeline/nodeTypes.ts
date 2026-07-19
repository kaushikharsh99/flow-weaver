import {
  FileText, Database, Globe, Cloud, FileSpreadsheet, Image as ImageIcon,
  Filter, Search, SlidersHorizontal, Shuffle,
  Wand2, Columns3, ArrowUpDown, GitMerge, Scissors,
  Copy, Fingerprint,
  Languages, Sparkles, Hash, MessageSquare, Type,
  Download, Save, Send, Upload,
} from "lucide-react";
import type { NodeTypeDef, MockPreview } from "./types";

const CAT_COLOR: Record<string, string> = {
  Loaders: "#4f86c6",
  Filters: "#c67a4f",
  Transform: "#7a4fc6",
  Dedup: "#4fc6a0",
  NLP: "#c64f86",
  Export: "#c6b74f",
};

// deterministic-ish random from a seed string
function seedRand(seed: string) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
  return () => {
    h += 0x6D2B79F5; let t = h;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const pick = <T,>(r: () => number, arr: T[]) => arr[Math.floor(r() * arr.length)];

const FIRST_NAMES = ["Ada","Alex","Sam","Priya","Kenji","Luca","Maya","Noah","Zara","Ivan","Yuki","Omar","Rosa","Theo","Nia"];
const LAST_NAMES = ["Nguyen","Patel","Kim","Silva","Rossi","Cohen","Weber","Duval","Okafor","Vega","Haas","Tanaka","Mori"];
const CITIES = ["Berlin","Tokyo","Lagos","Lima","Oslo","Kyoto","Porto","Austin","Cairo","Bogotá"];
const COMPANIES = ["Northwind","Acme","Contoso","Umbra","Globex","Initech","Hooli","Vandelay"];

function fakeUsers(seed: string, n: number): MockPreview {
  const r = seedRand(seed);
  const rows: (string | number)[][] = [];
  for (let i = 0; i < n; i++) {
    const f = pick(r, FIRST_NAMES), l = pick(r, LAST_NAMES);
    rows.push([1000 + i, `${f} ${l}`, `${f.toLowerCase()}@${pick(r, COMPANIES).toLowerCase()}.com`, pick(r, CITIES), Math.floor(r() * 60) + 18]);
  }
  return { kind: "table", columns: ["id","name","email","city","age"], rows, stats: { rows: n, columns: 5 } };
}

export const NODE_TYPES: NodeTypeDef[] = [
  // ------------------ Loaders
  {
    id: "load_csv", label: "Load CSV", category: "Loaders",
    description: "Read a CSV file from a URL or path",
    icon: FileSpreadsheet, color: CAT_COLOR.Loaders,
    inputs: [], outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "path", label: "File path", type: "text", default: "data/users.csv" },
      { key: "delimiter", label: "Delimiter", type: "select", default: ",", options: [
        { label: "Comma", value: "," }, { label: "Tab", value: "\t" }, { label: "Semicolon", value: ";" } ]},
      { key: "header", label: "Has header row", type: "boolean", default: true },
    ],
    mockOutput: (p) => fakeUsers("csv" + (p.path || ""), 8),
  },
  {
    id: "load_json", label: "Load JSON", category: "Loaders",
    description: "Parse a JSON array of records",
    icon: FileText, color: CAT_COLOR.Loaders,
    inputs: [], outputs: [{ id: "out", label: "records", type: "tabular" }],
    paramsSchema: [
      { key: "path", label: "File path", type: "text", default: "data/records.json" },
      { key: "root", label: "Root key", type: "text", default: "data", placeholder: "data" },
    ],
    mockOutput: (p) => fakeUsers("json" + (p.path || ""), 6),
  },
  {
    id: "http_fetch", label: "HTTP Fetch", category: "Loaders",
    description: "Fetch data from a REST endpoint",
    icon: Globe, color: CAT_COLOR.Loaders,
    inputs: [], outputs: [{ id: "out", label: "response", type: "any" }],
    paramsSchema: [
      { key: "url", label: "URL", type: "text", default: "https://api.example.com/v1/items" },
      { key: "method", label: "Method", type: "select", default: "GET", options: [
        { label: "GET", value: "GET" }, { label: "POST", value: "POST" } ]},
      { key: "timeout", label: "Timeout (ms)", type: "number", default: 5000, min: 100, max: 60000 },
    ],
    mockOutput: (p) => ({ kind: "stat", title: "HTTP 200 OK", stats: {
      "url": String(p.url || "-"), "latency": `${120 + Math.floor(Math.random()*200)}ms`, "bytes": `${(Math.random()*80+20).toFixed(1)} KB`,
    }}),
  },
  {
    id: "load_sql", label: "SQL Query", category: "Loaders",
    description: "Run a SELECT against a database",
    icon: Database, color: CAT_COLOR.Loaders,
    inputs: [], outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "query", label: "Query", type: "text", default: "SELECT * FROM users LIMIT 100" },
      { key: "limit", label: "Limit", type: "number", default: 100, min: 1, max: 10000 },
    ],
    mockOutput: (p) => fakeUsers("sql" + (p.query || ""), Math.min(10, p.limit || 10)),
  },
  {
    id: "load_s3", label: "S3 Bucket", category: "Loaders",
    description: "List and read objects from S3",
    icon: Cloud, color: CAT_COLOR.Loaders,
    inputs: [], outputs: [{ id: "out", label: "objects", type: "any" }],
    paramsSchema: [
      { key: "bucket", label: "Bucket", type: "text", default: "my-data-bucket" },
      { key: "prefix", label: "Prefix", type: "text", default: "raw/2024/" },
    ],
    mockOutput: (p) => ({ kind: "stat", title: "Listed objects", stats: {
      "bucket": String(p.bucket || "-"), "objects": 42, "total size": "128.4 MB",
    }}),
  },
  {
    id: "load_images", label: "Load Images", category: "Loaders",
    description: "Read a directory of images",
    icon: ImageIcon, color: CAT_COLOR.Loaders,
    inputs: [], outputs: [{ id: "out", label: "images", type: "image" }],
    paramsSchema: [
      { key: "path", label: "Directory", type: "text", default: "assets/photos" },
      { key: "recursive", label: "Recursive", type: "boolean", default: false },
    ],
    mockOutput: () => ({ kind: "stat", title: "Loaded images", stats: {
      "count": 128, "avg size": "412 KB", "formats": "jpg, png, webp",
    }}),
  },

  // ------------------ Filters
  {
    id: "filter_rows", label: "Filter Rows", category: "Filters",
    description: "Keep rows matching a condition",
    icon: Filter, color: CAT_COLOR.Filters,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "column", label: "Column", type: "text", default: "age" },
      { key: "op", label: "Operator", type: "select", default: ">", options: [
        { label: ">", value: ">"}, { label: "<", value: "<"}, { label: "=", value: "="}, { label: "!=", value: "!="} ]},
      { key: "value", label: "Value", type: "text", default: "25" },
    ],
    mockOutput: (p) => {
      const base = fakeUsers("filter" + JSON.stringify(p), 10);
      if (base.kind !== "table") return base;
      const kept = base.rows.filter((_, i) => i % 2 === 0);
      return { ...base, rows: kept, stats: { "rows in": 10, "rows out": kept.length, "kept": `${Math.round(kept.length/10*100)}%` }};
    },
  },
  {
    id: "search_text", label: "Search Text", category: "Filters",
    description: "Regex/substring filter on a text column",
    icon: Search, color: CAT_COLOR.Filters,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "matches", type: "tabular" }],
    paramsSchema: [
      { key: "column", label: "Column", type: "text", default: "email" },
      { key: "pattern", label: "Pattern", type: "text", default: "@acme\\.com$" },
      { key: "regex", label: "Regex", type: "boolean", default: true },
    ],
    mockOutput: (p) => {
      const base = fakeUsers("search" + JSON.stringify(p), 6);
      if (base.kind !== "table") return base;
      return { ...base, stats: { "matched": base.rows.length, "pattern": String(p.pattern || "") }};
    },
  },
  {
    id: "sample_rows", label: "Sample", category: "Filters",
    description: "Randomly sample N rows",
    icon: Shuffle, color: CAT_COLOR.Filters,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "n", label: "Sample size", type: "slider", default: 100, min: 1, max: 1000 },
      { key: "seed", label: "Seed", type: "number", default: 42, min: 0, max: 999999 },
    ],
    mockOutput: (p) => fakeUsers("sample" + p.seed, Math.min(8, p.n || 8)),
  },

  // ------------------ Transform
  {
    id: "select_columns", label: "Select Columns", category: "Transform",
    description: "Project a subset of columns",
    icon: Columns3, color: CAT_COLOR.Transform,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "columns", label: "Columns (comma sep)", type: "text", default: "id,name,email" },
    ],
    mockOutput: (p) => {
      const cols = String(p.columns || "id,name,email").split(",").map(c => c.trim());
      const base = fakeUsers("select" + p.columns, 8);
      if (base.kind !== "table") return base;
      const idx = cols.map(c => base.columns.indexOf(c)).filter(i => i >= 0);
      const columns = idx.map(i => base.columns[i]);
      const rows = base.rows.map(r => idx.map(i => r[i]));
      return { kind: "table", columns, rows, stats: { "columns": columns.length }};
    },
  },
  {
    id: "sort_rows", label: "Sort", category: "Transform",
    description: "Sort by a column",
    icon: ArrowUpDown, color: CAT_COLOR.Transform,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "column", label: "Column", type: "text", default: "age" },
      { key: "order", label: "Order", type: "select", default: "asc", options: [
        { label: "Ascending", value: "asc"}, { label: "Descending", value: "desc"} ]},
    ],
    mockOutput: (p) => {
      const base = fakeUsers("sort" + JSON.stringify(p), 8);
      if (base.kind !== "table") return base;
      const rows = [...base.rows].sort((a, b) => (a[4] as number) - (b[4] as number));
      if (p.order === "desc") rows.reverse();
      return { ...base, rows, stats: { "sorted by": String(p.column || ""), "order": String(p.order || "asc") }};
    },
  },
  {
    id: "join_rows", label: "Join", category: "Transform",
    description: "Join two tables on a key",
    icon: GitMerge, color: CAT_COLOR.Transform,
    inputs: [
      { id: "left", label: "left", type: "tabular", required: true },
      { id: "right", label: "right", type: "tabular", required: true },
    ],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "on", label: "Join key", type: "text", default: "id" },
      { key: "how", label: "How", type: "select", default: "inner", options: [
        { label: "Inner", value: "inner"}, { label: "Left", value: "left"}, { label: "Outer", value: "outer"} ]},
    ],
    mockOutput: (p) => fakeUsers("join" + JSON.stringify(p), 7),
  },
  {
    id: "split_col", label: "Split Column", category: "Transform",
    description: "Split a column by a delimiter",
    icon: Scissors, color: CAT_COLOR.Transform,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "column", label: "Column", type: "text", default: "name" },
      { key: "delim", label: "Delimiter", type: "text", default: " " },
    ],
    mockOutput: (p) => fakeUsers("split" + JSON.stringify(p), 6),
  },
  {
    id: "map_expr", label: "Map Expression", category: "Transform",
    description: "Compute a new column from an expression",
    icon: Wand2, color: CAT_COLOR.Transform,
    inputs: [{ id: "in", label: "rows", type: "any", required: true }],
    outputs: [{ id: "out", label: "rows", type: "any" }],
    paramsSchema: [
      { key: "target", label: "New column", type: "text", default: "full_name" },
      { key: "expr", label: "Expression", type: "text", default: "first + ' ' + last" },
    ],
    mockOutput: (p) => fakeUsers("map" + JSON.stringify(p), 6),
  },

  // ------------------ Dedup
  {
    id: "dedup_exact", label: "Dedup Exact", category: "Dedup",
    description: "Remove exact duplicate rows",
    icon: Copy, color: CAT_COLOR.Dedup,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "keys", label: "Keys (comma sep)", type: "text", default: "email" },
    ],
    mockOutput: (p) => {
      const before = 1000 + Math.floor(Math.random()*500);
      const removed = 30 + Math.floor(Math.random()*80);
      return { kind: "stat", title: "Deduplicated exact matches", stats: {
        "rows before": before, "rows after": before - removed, "removed": removed,
        "% removed": `${((removed/before)*100).toFixed(1)}%`, "keys": String(p.keys || ""),
      }};
    },
  },
  {
    id: "dedup_fuzzy", label: "Dedup Fuzzy", category: "Dedup",
    description: "Fuzzy-match near duplicates",
    icon: Fingerprint, color: CAT_COLOR.Dedup,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [{ id: "out", label: "rows", type: "tabular" }],
    paramsSchema: [
      { key: "column", label: "Column", type: "text", default: "name" },
      { key: "threshold", label: "Similarity threshold", type: "slider", default: 0.85, min: 0.5, max: 1, step: 0.01 },
    ],
    mockOutput: (p) => {
      const before = 500;
      const removed = Math.floor((1 - (p.threshold ?? 0.85)) * 500);
      return { kind: "stat", title: "Fuzzy deduplication", stats: {
        "rows before": before, "rows after": before - removed, "clusters merged": Math.floor(removed/2),
        "threshold": String(p.threshold ?? 0.85),
      }};
    },
  },
  {
    id: "normalize", label: "Normalize", category: "Dedup",
    description: "Normalize whitespace, case, encoding",
    icon: SlidersHorizontal, color: CAT_COLOR.Dedup,
    inputs: [{ id: "in", label: "rows", type: "any", required: true }],
    outputs: [{ id: "out", label: "rows", type: "any" }],
    paramsSchema: [
      { key: "lower", label: "Lowercase", type: "boolean", default: true },
      { key: "trim", label: "Trim whitespace", type: "boolean", default: true },
    ],
    mockOutput: () => ({ kind: "stat", title: "Normalized", stats: {
      "rows": 998, "changed": 214, "unchanged": 784,
    }}),
  },

  // ------------------ NLP
  {
    id: "tokenize", label: "Tokenize", category: "NLP",
    description: "Split text into tokens",
    icon: Type, color: CAT_COLOR.NLP,
    inputs: [{ id: "in", label: "text", type: "text", required: true }],
    outputs: [{ id: "out", label: "tokens", type: "any" }],
    paramsSchema: [
      { key: "model", label: "Tokenizer", type: "select", default: "bert", options: [
        { label: "BERT", value: "bert" }, { label: "GPT-BPE", value: "gpt" }, { label: "Whitespace", value: "ws" } ]},
    ],
    mockOutput: () => ({ kind: "text", snippets: [
      "The quick brown fox jumps over the lazy dog.",
      "Data pipelines are only as good as their inputs.",
    ], stats: { "tokens": 3421, "avg tokens/doc": 128, "vocab size": 30522 }, badges: ["en", "clean"] }),
  },
  {
    id: "detect_lang", label: "Detect Language", category: "NLP",
    description: "Identify text language",
    icon: Languages, color: CAT_COLOR.NLP,
    inputs: [{ id: "in", label: "text", type: "text", required: true }],
    outputs: [{ id: "out", label: "text+lang", type: "text" }],
    paramsSchema: [
      { key: "threshold", label: "Confidence", type: "slider", default: 0.9, min: 0, max: 1, step: 0.01 },
    ],
    mockOutput: () => ({ kind: "text", snippets: [
      "Bonjour, comment ça va aujourd'hui ?",
      "こんにちは、元気ですか？",
      "The rain in Spain stays mainly on the plain.",
    ], badges: ["fr", "ja", "en"], stats: { "docs": 512, "avg confidence": 0.94 }}),
  },
  {
    id: "sentiment", label: "Sentiment", category: "NLP",
    description: "Classify text sentiment",
    icon: Sparkles, color: CAT_COLOR.NLP,
    inputs: [{ id: "in", label: "text", type: "text", required: true }],
    outputs: [{ id: "out", label: "labeled", type: "text" }],
    paramsSchema: [
      { key: "model", label: "Model", type: "select", default: "distilbert", options: [
        { label: "DistilBERT", value: "distilbert" }, { label: "VADER", value: "vader" } ]},
    ],
    mockOutput: () => ({ kind: "stat", title: "Sentiment distribution", stats: {
      "positive": "62%", "neutral": "23%", "negative": "15%", "avg score": "+0.31",
    }}),
  },
  {
    id: "embed_text", label: "Embeddings", category: "NLP",
    description: "Generate vector embeddings",
    icon: Hash, color: CAT_COLOR.NLP,
    inputs: [{ id: "in", label: "text", type: "text", required: true }],
    outputs: [{ id: "out", label: "vectors", type: "any" }],
    paramsSchema: [
      { key: "model", label: "Model", type: "select", default: "mini-lm", options: [
        { label: "MiniLM (384)", value: "mini-lm" }, { label: "BGE (768)", value: "bge" } ]},
      { key: "batch", label: "Batch size", type: "number", default: 32, min: 1, max: 512 },
    ],
    mockOutput: (p) => ({ kind: "stat", title: "Embeddings generated", stats: {
      "vectors": 1024, "dim": p.model === "bge" ? 768 : 384, "time/vec": "3.2ms",
    }}),
  },
  {
    id: "summarize", label: "Summarize", category: "NLP",
    description: "Abstractive summarization",
    icon: MessageSquare, color: CAT_COLOR.NLP,
    inputs: [{ id: "in", label: "text", type: "text", required: true }],
    outputs: [{ id: "out", label: "summaries", type: "text" }],
    paramsSchema: [
      { key: "maxLen", label: "Max length", type: "slider", default: 120, min: 30, max: 400 },
    ],
    mockOutput: () => ({ kind: "text", snippets: [
      "Quarterly revenue rose 12% driven by APAC expansion; margins held flat.",
      "The paper proposes a new attention variant that reduces memory by 40%.",
    ], stats: { "docs": 128, "avg length": 96, "compression": "8.4×" }}),
  },

  // ------------------ Export
  {
    id: "write_csv", label: "Write CSV", category: "Export",
    description: "Write rows to CSV file",
    icon: Save, color: CAT_COLOR.Export,
    inputs: [{ id: "in", label: "rows", type: "tabular", required: true }],
    outputs: [],
    paramsSchema: [
      { key: "path", label: "Output path", type: "text", default: "out/results.csv" },
      { key: "compress", label: "Gzip", type: "boolean", default: false },
    ],
    mockOutput: (p) => ({ kind: "file", name: String(p.path || "out.csv"), format: "CSV", size: `${(Math.random()*4+1).toFixed(1)} MB`, rows: 4213,
      stats: { "written": 4213, "compressed": p.compress ? "yes" : "no" } }),
  },
  {
    id: "write_json", label: "Write JSON", category: "Export",
    description: "Serialize records to JSON",
    icon: Download, color: CAT_COLOR.Export,
    inputs: [{ id: "in", label: "rows", type: "any", required: true }],
    outputs: [],
    paramsSchema: [
      { key: "path", label: "Output path", type: "text", default: "out/results.json" },
      { key: "pretty", label: "Pretty print", type: "boolean", default: true },
    ],
    mockOutput: (p) => ({ kind: "file", name: String(p.path || "out.json"), format: "JSON", size: `${(Math.random()*3+1).toFixed(1)} MB`, rows: 2100 }),
  },
  {
    id: "webhook", label: "Send Webhook", category: "Export",
    description: "POST rows to an endpoint",
    icon: Send, color: CAT_COLOR.Export,
    inputs: [{ id: "in", label: "rows", type: "any", required: true }],
    outputs: [],
    paramsSchema: [
      { key: "url", label: "Webhook URL", type: "text", default: "https://hooks.example.com/pipeline" },
      { key: "batch", label: "Batch size", type: "number", default: 100, min: 1, max: 1000 },
    ],
    mockOutput: (p) => ({ kind: "stat", title: "Webhook delivered", stats: {
      "requests": 42, "success": 41, "failed": 1, "url": String(p.url || "-"),
    }}),
  },
  {
    id: "upload_s3", label: "Upload S3", category: "Export",
    description: "Upload files to S3",
    icon: Upload, color: CAT_COLOR.Export,
    inputs: [{ id: "in", label: "data", type: "any", required: true }],
    outputs: [],
    paramsSchema: [
      { key: "bucket", label: "Bucket", type: "text", default: "processed-data" },
      { key: "key", label: "Key", type: "text", default: "runs/{date}/output.parquet" },
    ],
    mockOutput: (p) => ({ kind: "file", name: String(p.key || "output"), format: "PARQUET", size: `${(Math.random()*20+5).toFixed(1)} MB` }),
  },
];

export const NODE_TYPE_MAP: Record<string, NodeTypeDef> = Object.fromEntries(
  NODE_TYPES.map(n => [n.id, n]),
);

export const CATEGORIES: import("./types").Category[] = ["Loaders","Filters","Transform","Dedup","NLP","Export"];

export const CATEGORY_COLOR = CAT_COLOR;

export const PORT_TYPE_COLOR: Record<string, string> = {
  tabular: "#4f86c6",
  text: "#c64f86",
  image: "#7a4fc6",
  audio: "#4fc6a0",
  any: "#8a8a92",
};

export function typesCompatible(a?: string, b?: string) {
  if (!a || !b) return false;
  if (a === "any" || b === "any") return true;
  return a === b;
}

import * as LucideIcons from "lucide-react";

export function getIcon(icon: any): LucideIcons.LucideIcon {
  if (typeof icon === "string") {
    // Map string names to Lucide icons
    const Icon = (LucideIcons as any)[icon];
    return Icon || LucideIcons.HelpCircle;
  }
  return icon || LucideIcons.HelpCircle;
}
