// --- Common ---
export interface ApiResponse<T> { data: T }
export interface ApiListResponse<T> { data: T[]; meta: { total: number } }
export interface ApiError { error: { code: string; message: string; details?: { field: string; issue: string }[] } }

// --- Projects ---
export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}
export interface CreateProjectRequest { name: string; description?: string }
export interface UpdateProjectRequest { name?: string; description?: string }

// --- Pipelines ---
// Pipeline summary (for list views - no nodes/edges)
export interface PipelineSummary {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

// Full pipeline (includes nodes, edges, viewport, variables, settings)
// This aligns with the v1.0.0 pipeline format spec
export interface Pipeline {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  variables?: Record<string, string | number | boolean | null>;
  settings?: PipelineSettings;
  viewport?: Viewport;
}

export interface PipelineNode {
  id: string;
  type: 'pipelineNode' | 'commentNode';
  position: { x: number; y: number };
  data: {
    typeId: string;
    title: string;
    params: Record<string, any>;
    collapsed?: boolean;
    disabled?: boolean;
    colorLabel?: string;
    comment?: string;
    width?: number;
    height?: number;
  };
}

export interface PipelineEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle: string;
  targetHandle: string;
}

export interface PipelineSettings {
  maxConcurrency?: number;
  timeoutMs?: number;
}

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

export interface CreatePipelineRequest {
  name: string;
  description?: string;
  nodes?: PipelineNode[];
  edges?: PipelineEdge[];
}

export interface UpdatePipelineRequest {
  name?: string;
  description?: string;
  nodes?: PipelineNode[];
  edges?: PipelineEdge[];
  variables?: Record<string, string | number | boolean | null>;
  settings?: PipelineSettings;
  viewport?: Viewport;
}

// --- Executions ---
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Execution {
  id: string;
  pipelineId: string;
  status: ExecutionStatus;
  progress: number;
  startedAt: string;
  completedAt: string | null;
}

export interface StartExecutionRequest {
  variables?: Record<string, any>;
}

export interface ExecutionLogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  nodeId?: string;
  message: string;
}

// --- WebSocket Events ---
export type ExecutionEvent =
  | { type: 'EXECUTION_STARTED'; timestamp: string }
  | { type: 'NODE_UPDATE'; nodeId: string; status: string; progress?: number; preview?: any }
  | { type: 'LOG'; level: string; nodeId?: string; message: string }
  | { type: 'EXECUTION_COMPLETED'; timestamp: string }
  | { type: 'EXECUTION_FAILED'; error: string; timestamp: string };

// --- Node Types (from registry) ---
export interface NodeTypeInfo {
  type: string;
  category: string;
  label: string;
  description: string;
}

export interface NodeTypeDetail extends NodeTypeInfo {
  inputs: { id: string; label: string; type: string; required?: boolean }[];
  outputs: { id: string; label: string; type: string }[];
  parameters: any[];
}

// --- Plugins ---
export interface Plugin {
  id: string;
  name: string;
  version: string;
  author: string;
  nodes: string[];
}

// --- Templates ---
export interface Template {
  id: string;
  name: string;
  description: string;
  pipelineData?: { nodes: PipelineNode[]; edges: PipelineEdge[] };
}

export interface CreateTemplateRequest {
  pipelineId: string;
  name: string;
  description?: string;
}
