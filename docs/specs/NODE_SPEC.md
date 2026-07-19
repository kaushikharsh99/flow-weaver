# Phase 4: Node Specification v1.0

## 1. Introduction

This document defines the **Universal Node Contract** for FlowWeaver. It establishes the API and lifecycle that every node—whether built-in or provided by third-party plugins—must adhere to. By decoupling node definitions from their execution logic, this specification ensures a robust, extensible, and type-safe ecosystem for visual pipeline authoring.

## 2. Architecture: Definition vs. Implementation

FlowWeaver strictly separates a node's **Definition** (its static metadata, schema, and UI representation) from its **Implementation** (the actual execution logic).

- **Node Definition**: Controls how the node appears in the canvas, its configuration parameters, and its static/dynamic port structures. It is heavily utilized by the frontend to render the UI, validate connections, and run simulated mock outputs without loading heavy backend logic.
- **Node Implementation**: Provides the `execute()` function and handles data processing, error handling, progress reporting, and streaming. This is the core runtime logic.

## 3. Node Lifecycle

1. **Registration**: Nodes are registered into the `NodeRegistry` with their Definition and optionally their Implementation.
2. **Validation**: The canvas validates connections based on the node's port types and parameter validation rules.
3. **Configuration**: Users interact with the canvas to set parameters. Dynamic ports may re-evaluate based on parameter changes.
4. **Execution**: The runtime constructs an `ExecutionContext` and invokes the node's `execute()` function.
5. **Result**: The node returns a `NodeResult` (or streams data), which is passed to downstream nodes.

## 4. TypeScript Interfaces

### 4.1. Core Types

```typescript
export type PortType = 'tabular' | 'text' | 'image' | 'audio' | 'any';
export type Category = 'Loaders' | 'Filters' | 'Transform' | 'Dedup' | 'NLP' | 'Export';

export interface Port {
  id: string;
  label: string;
  type: PortType;
  required?: boolean;
  description?: string;
}

export type ParamField =
  | { key: string; label: string; type: 'text'; default?: string; placeholder?: string; required?: boolean }
  | { key: string; label: string; type: 'number'; default?: number; min?: number; max?: number; step?: number; required?: boolean }
  | { key: string; label: string; type: 'select'; default?: string; options: { label: string; value: string }[]; required?: boolean }
  | { key: string; label: string; type: 'boolean'; default?: boolean; required?: boolean }
  | { key: string; label: string; type: 'slider'; default?: number; min: number; max: number; step?: number; required?: boolean }
  | { key: string; label: string; type: 'custom'; componentId: string; default?: any; required?: boolean }; // Custom UI Component support
```

### 4.2. Node Definition

```typescript
export interface NodeVersion {
  major: number;
  minor: number;
  patch: number;
}

export interface NodeDefinition {
  id: string;
  version: NodeVersion;
  label: string;
  category: Category;
  description: string;
  icon: string; // e.g., LucideIcon name
  color: string;
  
  // Static Ports
  inputs: Port[];
  outputs: Port[];
  
  // Dynamic Ports (re-calculated when parameters or input structure changes)
  getDynamicInputs?: (params: Record<string, any>) => Port[];
  getDynamicOutputs?: (params: Record<string, any>) => Port[];
  
  paramsSchema: ParamField[];
  
  // Advanced Validation Rules
  validate?: (params: Record<string, any>, inputs: Record<string, Port>) => ValidationResult;
  
  // Documentation for Node Authors / Users
  docs?: {
    summary: string;
    examples: { title: string; description: string; params: Record<string, any> }[];
  };
  
  // Mock Preview for UI rendering without backend
  mockOutput?: (params: Record<string, any>, inputSample?: any) => MockPreview;
}

export interface ValidationResult {
  isValid: boolean;
  errors?: { paramKey?: string; message: string }[];
}

export interface MockPreview {
  // Simplified mock data representation structure
  type: PortType;
  data: any;
}
```

### 4.3. Node Implementation & Execution Contract

The runtime passes an `ExecutionContext` to every node when executed.

```typescript
export interface ExecutionContext {
  // Inputs mapped by Port ID
  inputs: Record<string, any>; 
  
  // Evaluated parameters for the node
  params: Record<string, any>;
  
  // Services for progress reporting and logging
  reportProgress: (percent: number, message?: string) => void;
  log: (level: 'info' | 'warn' | 'error', message: string) => void;
  
  // Support for graceful termination
  signal: AbortSignal;
  
  // Output streaming mechanism
  streamOutput: (portId: string, chunk: any) => void;
}

export interface NodeResult {
  // Outputs mapped by Port ID
  outputs: Record<string, any>;
}

export interface NodeImplementation {
  id: string; // Must match NodeDefinition id
  version: NodeVersion; // Must match NodeDefinition version
  
  execute(context: ExecutionContext): Promise<NodeResult>;
}
```

## 5. Execution Contract Details

### 5.1. The `execute()` Function
- **Asynchronous**: Must return a `Promise<NodeResult>`.
- **Stateless**: The function should not rely on external state mutations. All dependencies are provided via the `ExecutionContext`.
- **Cancellation**: Must respect `context.signal.aborted` for long-running operations. Nodes should periodically check this token and throw if aborted.

### 5.2. Error Handling
- Nodes should throw standard `Error` objects or specific `NodeExecutionError` instances with clear user-facing messages.
- Do not catch and suppress critical errors silently. Let the runtime catch and route them to the UI logs.
- Validation of parameters during runtime should be the first step in `execute()`.

### 5.3. Progress & Streaming
- `context.reportProgress(percent)` enables visual progress bars on the canvas.
- `context.streamOutput(portId, chunk)` can be used for LLM tokens, large file reading, or batch processing before the final `Promise` resolves. Consumers can listen to these streams.

## 6. Data Types & Payloads

Data flowing between nodes (via ports) must conform to predictable structures based on their `PortType`.

| Port Type | Payload Structure (Example) |
|---|---|
| `tabular` | `Array<Record<string, any>>` (e.g., CSV/DB rows) |
| `text` | `string` |
| `image` | `Buffer` or `{ url: string, metadata: object }` |
| `audio` | `Buffer` or `{ url: string, metadata: object }` |
| `any` | Polymorphic, relies on node logic to validate at runtime. |

## 7. Complete Example: Regex Filter Node

### The Definition
```typescript
export const regexFilterDefinition: NodeDefinition = {
  id: 'regex-filter',
  version: { major: 1, minor: 0, patch: 0 },
  label: 'Regex Filter',
  category: 'Filters',
  description: 'Filters tabular data rows using a regular expression.',
  icon: 'Regex', // Identifier for the LucideIcon
  color: '#4F46E5', // Indigo
  
  inputs: [
    { id: 'data', label: 'Data', type: 'tabular', required: true }
  ],
  outputs: [
    { id: 'filtered', label: 'Filtered Data', type: 'tabular' },
    { id: 'rejected', label: 'Rejected Data', type: 'tabular' }
  ],
  
  paramsSchema: [
    { key: 'targetColumn', label: 'Column to Match', type: 'text', required: true },
    { key: 'pattern', label: 'Regex Pattern', type: 'text', required: true },
    { key: 'caseInsensitive', label: 'Case Insensitive', type: 'boolean', default: false }
  ],
  
  validate: (params) => {
    try {
      new RegExp(params.pattern);
      return { isValid: true };
    } catch (e) {
      return { isValid: false, errors: [{ paramKey: 'pattern', message: 'Invalid Regex pattern.' }] };
    }
  },
  
  docs: {
    summary: 'Splits rows based on a regex pattern match.',
    examples: [
      {
        title: 'Filter emails',
        description: 'Keep rows where email ends with @gmail.com',
        params: { targetColumn: 'email', pattern: '.*@gmail\\.com$', caseInsensitive: true }
      }
    ]
  },
  
  mockOutput: (params) => {
    return {
      type: 'tabular',
      data: [{ [params.targetColumn || 'col']: 'mock_match_data' }]
    };
  }
};
```

### The Implementation
```typescript
export const regexFilterImplementation: NodeImplementation = {
  id: 'regex-filter',
  version: { major: 1, minor: 0, patch: 0 },
  
  execute: async (context: ExecutionContext): Promise<NodeResult> => {
    const { inputs, params, reportProgress, log, signal } = context;
    const data = inputs.data as Array<Record<string, any>>;
    const { targetColumn, pattern, caseInsensitive } = params;
    
    if (!targetColumn || !pattern) {
      throw new Error('Target column and pattern are required.');
    }
    
    log('info', `Starting regex filter on column "${targetColumn}"`);
    
    const flags = caseInsensitive ? 'i' : '';
    const regex = new RegExp(pattern, flags);
    
    const filtered = [];
    const rejected = [];
    
    for (let i = 0; i < data.length; i++) {
      // Respect the abort signal
      if (signal.aborted) {
        log('warn', 'Execution aborted by user.');
        throw new Error('Execution aborted');
      }
      
      const row = data[i];
      const value = String(row[targetColumn] || '');
      
      if (regex.test(value)) {
        filtered.push(row);
      } else {
        rejected.push(row);
      }
      
      // Report progress every 100 rows
      if (i % 100 === 0) {
        reportProgress(Math.round((i / data.length) * 100));
      }
    }
    
    reportProgress(100);
    log('info', `Filtered ${filtered.length} rows, rejected ${rejected.length} rows.`);
    
    return {
      outputs: {
        filtered,
        rejected
      }
    };
  }
};
```
