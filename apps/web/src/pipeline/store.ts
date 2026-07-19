import { create } from "zustand";
import type { Edge, Node, XYPosition } from "reactflow";
import { addEdge, applyEdgeChanges, applyNodeChanges } from "reactflow";
import type { EdgeChange, NodeChange, Connection } from "reactflow";
import { NODE_TYPE_MAP } from "./nodeTypes";
import type { NodeRuntime, NodeStatus, MockPreview } from "./types";
import { api } from '../api';
import type { Pipeline as ApiPipeline, PipelineNode as ApiPipelineNode, PipelineEdge as ApiPipelineEdge } from '../api/types';
import {
  SIDEBAR_DEFAULT_WIDTH, SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH,
  GRID_SIZE, COMMENT_NODE_DEFAULT_WIDTH, COMMENT_NODE_DEFAULT_HEIGHT,
  HISTORY_MAX_SIZE, PIPELINE_SCHEMA_URL, PIPELINE_FORMAT_VERSION,
  NODE_PASTE_OFFSET, MAX_RECENT_NODE_TYPES,
} from './constants';
export interface PipelineNodeData {
  typeId: string;
  title: string;
  params: Record<string, any>;
  runtime: NodeRuntime;
  collapsed?: boolean;
  disabled?: boolean;
  colorLabel?: string;
  comment?: string; // for comment nodes; typeId will be "__comment"
  width?: number;
  height?: number;
}

export type PipelineNode = Node<PipelineNodeData>;

export interface Tab {
  id: string;
  name: string;
  nodes: PipelineNode[];
  edges: Edge[];
}

interface HistorySnapshot {
  nodes: PipelineNode[];
  edges: Edge[];
}

interface UIState {
  sidebarWidth: number;
  sidebarCollapsed: boolean;
  inspectorOpen: boolean;
  snapToGrid: boolean;
  theme: "dark" | "light";
  paletteOpen: boolean;
  recentNodeTypeIds: string[];
}

interface PipelineStore {
  tabs: Tab[];
  activeTabId: string;
  selectedIds: string[];
  ui: UIState;
  running: boolean;
  projectId: string | null;
  pipelineId: string | null;
  clipboard: PipelineNode[];
  history: HistorySnapshot[];
  future: HistorySnapshot[];

  // getters helpers
  activeTab: () => Tab;

  // canvas mutations
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (c: Connection) => void;
  addNode: (typeId: string, position: XYPosition) => void;
  addCommentNode: (position: XYPosition) => void;
  updateNodeParams: (nodeId: string, params: Record<string, any>) => void;
  updateNodeTitle: (nodeId: string, title: string) => void;
  setNodeCollapsed: (nodeId: string, v: boolean) => void;
  setNodeColorLabel: (nodeId: string, color: string | undefined) => void;
  setNodeDisabled: (nodeId: string, v: boolean) => void;
  updateCommentText: (nodeId: string, text: string) => void;
  setSelected: (ids: string[]) => void;
  duplicateSelection: () => void;
  copySelection: () => void;
  paste: (offset?: XYPosition) => void;
  deleteSelection: () => void;
  nudgeSelection: (dx: number, dy: number) => void;
  selectAll: () => void;
  clearCanvas: () => void;

  // runtime
  setRuntime: (nodeId: string, r: Partial<NodeRuntime>) => void;
  setAllRuntimeIdle: () => void;
  markDownstreamStale: (nodeId: string) => void;
  setRunning: (v: boolean) => void;

  // ui
  setSidebarWidth: (w: number) => void;
  toggleSidebar: () => void;
  setInspectorOpen: (v: boolean) => void;
  setSnapToGrid: (v: boolean) => void;
  setTheme: (t: "dark" | "light") => void;
  setPaletteOpen: (v: boolean) => void;
  pushRecentNodeType: (id: string) => void;

  // tabs
  addTab: () => void;
  closeTab: (id: string) => void;
  setActiveTab: (id: string) => void;
  renameActiveTab: (name: string) => void;

  // history
  pushHistory: () => void;
  undo: () => void;
  redo: () => void;

  // save/load
  exportJSON: () => string;
  importJSON: (json: string) => void;

  // persistence (async, via API)
  savePipelineToServer: () => Promise<void>;
  loadPipelineFromServer: (pipelineId: string) => Promise<void>;
  createNewPipeline: (name?: string) => Promise<void>;
}

const genId = () => Math.random().toString(36).slice(2, 10);

const makeTab = (name = "Untitled Pipeline"): Tab => ({
  id: genId(),
  name,
  nodes: [],
  edges: [],
});

function snap(v: number, grid = GRID_SIZE) { return Math.round(v / grid) * grid; }

export const useStore = create<PipelineStore>((set, get) => {
  const firstTab = makeTab("My Pipeline");
  return {
    tabs: [firstTab],
    activeTabId: firstTab.id,
    selectedIds: [],
    ui: {
      sidebarWidth: SIDEBAR_DEFAULT_WIDTH,
      sidebarCollapsed: false,
      inspectorOpen: true,
      snapToGrid: false,
      theme: "dark",
      paletteOpen: false,
      recentNodeTypeIds: [],
    },
    running: false,
    projectId: null,
    pipelineId: null,
    clipboard: [],
    history: [],
    future: [],

    activeTab: () => {
      const s = get();
      return s.tabs.find(t => t.id === s.activeTabId) || s.tabs[0];
    },

    onNodesChange: (changes) => {
      // detect end of drag to push history
      const isDragEnd = changes.some(c => c.type === "position" && (c as any).dragging === false);
      if (isDragEnd) get().pushHistory();
      set(state => {
        const tab = state.tabs.find(t => t.id === state.activeTabId)!;
        const nodes = applyNodeChanges(changes, tab.nodes) as PipelineNode[];
        return { tabs: state.tabs.map(t => t.id === tab.id ? { ...t, nodes } : t) };
      });
    },
    onEdgesChange: (changes) => {
      const structural = changes.some(c => c.type === "remove");
      if (structural) get().pushHistory();
      set(state => {
        const tab = state.tabs.find(t => t.id === state.activeTabId)!;
        const edges = applyEdgeChanges(changes, tab.edges);
        return { tabs: state.tabs.map(t => t.id === tab.id ? { ...t, edges } : t) };
      });
    },
    onConnect: (c) => {
      get().pushHistory();
      set(state => {
        const tab = state.tabs.find(t => t.id === state.activeTabId)!;
        const edges = addEdge({ ...c, type: "smoothstep", animated: false }, tab.edges);
        return { tabs: state.tabs.map(t => t.id === tab.id ? { ...t, edges } : t) };
      });
    },

    addNode: (typeId, position) => {
      const def = NODE_TYPE_MAP[typeId];
      if (!def) return;
      get().pushHistory();
      const params: Record<string, any> = {};
      def.paramsSchema.forEach(f => { if ("default" in f && f.default !== undefined) params[f.key] = f.default; });
      const snapOn = get().ui.snapToGrid;
      const pos = snapOn ? { x: snap(position.x), y: snap(position.y) } : position;
      const newNode: PipelineNode = {
        id: genId(),
        type: "pipelineNode",
        position: pos,
        data: {
          typeId,
          title: def.label,
          params,
          runtime: { status: "idle" },
        },
      };
      set(state => ({
        tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, nodes: [...t.nodes, newNode] } : t),
        selectedIds: [newNode.id],
      }));
    },
    addCommentNode: (position) => {
      get().pushHistory();
      const newNode: PipelineNode = {
        id: genId(),
        type: "commentNode",
        position,
        data: {
          typeId: "__comment",
          title: "Note",
          params: {},
          runtime: { status: "idle" },
          comment: "Double-click to edit…",
          width: COMMENT_NODE_DEFAULT_WIDTH, height: COMMENT_NODE_DEFAULT_HEIGHT,
        },
      };
      set(state => ({
        tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, nodes: [...t.nodes, newNode] } : t),
        selectedIds: [newNode.id],
      }));
    },
    updateNodeParams: (nodeId, params) => {
      get().pushHistory();
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t,
          nodes: t.nodes.map(n => n.id !== nodeId ? n : {
            ...n, data: { ...n.data, params: { ...n.data.params, ...params },
              runtime: n.data.runtime.status === "success" || n.data.runtime.status === "cached"
                ? { ...n.data.runtime, status: "stale" as NodeStatus }
                : n.data.runtime,
            },
          }),
        }),
      }));
      get().markDownstreamStale(nodeId);
    },
    updateNodeTitle: (nodeId, title) => {
      get().pushHistory();
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => n.id === nodeId ? { ...n, data: { ...n.data, title } } : n)
        }),
      }));
    },
    setNodeCollapsed: (nodeId, v) => {
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => n.id === nodeId ? { ...n, data: { ...n.data, collapsed: v } } : n)
        }),
      }));
    },
    setNodeColorLabel: (nodeId, color) => {
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => n.id === nodeId ? { ...n, data: { ...n.data, colorLabel: color } } : n)
        }),
      }));
    },
    setNodeDisabled: (nodeId, v) => {
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => n.id === nodeId ? { ...n, data: { ...n.data, disabled: v } } : n)
        }),
      }));
    },
    updateCommentText: (nodeId, text) => {
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => n.id === nodeId ? { ...n, data: { ...n.data, comment: text } } : n)
        }),
      }));
    },

    setSelected: (ids) => set({ selectedIds: ids }),

    copySelection: () => {
      const tab = get().activeTab();
      const sel = tab.nodes.filter(n => get().selectedIds.includes(n.id));
      set({ clipboard: JSON.parse(JSON.stringify(sel)) });
    },
    paste: (offset = NODE_PASTE_OFFSET) => {
      const cb = get().clipboard;
      if (!cb.length) return;
      get().pushHistory();
      const newNodes: PipelineNode[] = cb.map(n => ({
        ...n, id: genId(),
        position: { x: n.position.x + offset.x, y: n.position.y + offset.y },
        data: { ...n.data, runtime: { status: "idle" as NodeStatus } },
        selected: true,
      }));
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : { ...t, nodes: [...t.nodes, ...newNodes] }),
        selectedIds: newNodes.map(n => n.id),
      }));
    },
    duplicateSelection: () => {
      get().copySelection();
      get().paste({ x: 40, y: 40 });
    },
    deleteSelection: () => {
      const ids = get().selectedIds;
      if (!ids.length) return;
      get().pushHistory();
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t,
          nodes: t.nodes.filter(n => !ids.includes(n.id)),
          edges: t.edges.filter(e => !ids.includes(e.source) && !ids.includes(e.target)),
        }),
        selectedIds: [],
      }));
    },
    nudgeSelection: (dx, dy) => {
      const ids = get().selectedIds;
      if (!ids.length) return;
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => ids.includes(n.id) ? { ...n, position: { x: n.position.x + dx, y: n.position.y + dy } } : n)
        }),
      }));
    },
    selectAll: () => {
      const tab = get().activeTab();
      set({ selectedIds: tab.nodes.map(n => n.id) });
    },
    clearCanvas: () => {
      get().pushHistory();
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : { ...t, nodes: [], edges: [] }),
        selectedIds: [],
      }));
    },

    setRuntime: (nodeId, r) => {
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => n.id === nodeId ? {
            ...n, data: { ...n.data, runtime: { ...n.data.runtime, ...r } }
          } : n)
        }),
      }));
    },
    setAllRuntimeIdle: () => {
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => ({ ...n, data: { ...n.data, runtime: { status: "idle" as NodeStatus } } }))
        }),
      }));
    },
    markDownstreamStale: (nodeId) => {
      const tab = get().activeTab();
      const outgoing = new Map<string, string[]>();
      for (const e of tab.edges) {
        const arr = outgoing.get(e.source) || [];
        arr.push(e.target); outgoing.set(e.source, arr);
      }
      const toStale = new Set<string>();
      const walk = (id: string) => {
        for (const t of outgoing.get(id) || []) if (!toStale.has(t)) { toStale.add(t); walk(t); }
      };
      walk(nodeId);
      set(state => ({
        tabs: state.tabs.map(t => t.id !== state.activeTabId ? t : {
          ...t, nodes: t.nodes.map(n => toStale.has(n.id) && (n.data.runtime.status === "success" || n.data.runtime.status === "cached")
            ? { ...n, data: { ...n.data, runtime: { ...n.data.runtime, status: "stale" as NodeStatus } } } : n)
        }),
      }));
    },
    setRunning: (v) => set({ running: v }),

    setSidebarWidth: (w) => set(state => ({ ui: { ...state.ui, sidebarWidth: Math.max(SIDEBAR_MIN_WIDTH, Math.min(SIDEBAR_MAX_WIDTH, w)) } })),
    toggleSidebar: () => set(state => ({ ui: { ...state.ui, sidebarCollapsed: !state.ui.sidebarCollapsed } })),
    setInspectorOpen: (v) => set(state => ({ ui: { ...state.ui, inspectorOpen: v } })),
    setSnapToGrid: (v) => set(state => ({ ui: { ...state.ui, snapToGrid: v } })),
    setTheme: (t) => set(state => ({ ui: { ...state.ui, theme: t } })),
    setPaletteOpen: (v) => set(state => ({ ui: { ...state.ui, paletteOpen: v } })),
    pushRecentNodeType: (id) => set(state => {
      const filtered = state.ui.recentNodeTypeIds.filter(x => x !== id);
      return { ui: { ...state.ui, recentNodeTypeIds: [id, ...filtered].slice(0, MAX_RECENT_NODE_TYPES) } };
    }),

    addTab: () => {
      const t = makeTab(`Pipeline ${get().tabs.length + 1}`);
      set(state => ({ tabs: [...state.tabs, t], activeTabId: t.id, selectedIds: [], history: [], future: [] }));
    },
    closeTab: (id) => {
      set(state => {
        if (state.tabs.length === 1) return state;
        const idx = state.tabs.findIndex(t => t.id === id);
        const tabs = state.tabs.filter(t => t.id !== id);
        const newActive = state.activeTabId === id ? tabs[Math.max(0, idx - 1)].id : state.activeTabId;
        return { tabs, activeTabId: newActive, selectedIds: [], history: [], future: [] };
      });
    },
    setActiveTab: (id) => set({ activeTabId: id, selectedIds: [], history: [], future: [] }),
    renameActiveTab: (name) => set(state => ({
      tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, name } : t),
    })),

    pushHistory: () => {
      const tab = get().activeTab();
      const snap: HistorySnapshot = {
        nodes: JSON.parse(JSON.stringify(tab.nodes)),
        edges: JSON.parse(JSON.stringify(tab.edges)),
      };
      set(state => ({ history: [...state.history, snap].slice(-HISTORY_MAX_SIZE), future: [] }));
    },
    undo: () => {
      const hist = get().history;
      if (!hist.length) return;
      const prev = hist[hist.length - 1];
      const tab = get().activeTab();
      const current: HistorySnapshot = { nodes: JSON.parse(JSON.stringify(tab.nodes)), edges: JSON.parse(JSON.stringify(tab.edges)) };
      set(state => ({
        history: state.history.slice(0, -1),
        future: [...state.future, current],
        tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, nodes: prev.nodes, edges: prev.edges } : t),
        selectedIds: [],
      }));
    },
    redo: () => {
      const fut = get().future;
      if (!fut.length) return;
      const next = fut[fut.length - 1];
      const tab = get().activeTab();
      const current: HistorySnapshot = { nodes: JSON.parse(JSON.stringify(tab.nodes)), edges: JSON.parse(JSON.stringify(tab.edges)) };
      set(state => ({
        future: state.future.slice(0, -1),
        history: [...state.history, current],
        tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, nodes: next.nodes, edges: next.edges } : t),
        selectedIds: [],
      }));
    },

    exportJSON: () => {
      const tab = get().activeTab();
      return JSON.stringify({
        $schema: PIPELINE_SCHEMA_URL,
        version: PIPELINE_FORMAT_VERSION,
        id: get().pipelineId || genId(),
        name: tab.name,
        description: '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        nodes: tab.nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: {
          typeId: n.data.typeId, title: n.data.title, params: n.data.params, collapsed: n.data.collapsed,
          disabled: n.data.disabled, colorLabel: n.data.colorLabel, comment: n.data.comment,
          width: n.data.width, height: n.data.height,
        }})),
        edges: tab.edges.map(e => ({ id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle })),
        variables: {},
        settings: {},
        viewport: { x: 0, y: 0, zoom: 1 },
      }, null, 2);
    },
    importJSON: (json) => {
      const data = JSON.parse(json);
      if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) throw new Error('Malformed pipeline file');
      get().pushHistory();
      const nodes: PipelineNode[] = data.nodes.map((n: any) => ({
        id: n.id, type: n.type || 'pipelineNode', position: n.position,
        data: { ...n.data, runtime: { status: 'idle' as NodeStatus } },
      }));
      const edges: Edge[] = data.edges.map((e: any) => ({ ...e, type: 'smoothstep' }));
      set(state => ({
        tabs: state.tabs.map(t => t.id === state.activeTabId ? { ...t, name: data.name || t.name, nodes, edges } : t),
        pipelineId: data.id || null,
        selectedIds: [],
      }));
    },

    savePipelineToServer: async () => {
      const tab = get().activeTab();
      const pipelineId = get().pipelineId;
      const projectId = get().projectId;
      
      const pipelineData = {
        name: tab.name,
        nodes: tab.nodes.map(n => ({
          id: n.id,
          type: n.type as 'pipelineNode' | 'commentNode',
          position: n.position,
          data: {
            typeId: n.data.typeId,
            title: n.data.title,
            params: n.data.params,
            collapsed: n.data.collapsed,
            disabled: n.data.disabled,
            colorLabel: n.data.colorLabel,
            comment: n.data.comment,
            width: n.data.width,
            height: n.data.height,
          },
        })),
        edges: tab.edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || '',
          targetHandle: e.targetHandle || '',
        })),
        viewport: { x: 0, y: 0, zoom: 1 },
      };

      if (pipelineId) {
        await api.updatePipeline(pipelineId, pipelineData);
      } else {
        // Auto-create project if needed
        let pid = projectId;
        if (!pid) {
          const { data: projects } = await api.listProjects();
          if (projects.length > 0) {
            pid = projects[0].id;
          } else {
            const { data: proj } = await api.createProject({ name: 'My Projects' });
            pid = proj.id;
          }
          set({ projectId: pid });
        }
        const { data: created } = await api.createPipeline(pid!, {
          ...pipelineData,
        });
        set({ pipelineId: created.id });
      }
    },

    loadPipelineFromServer: async (pipelineId) => {
      const { data: pipeline } = await api.getPipeline(pipelineId);
      get().pushHistory();
      const nodes: PipelineNode[] = pipeline.nodes.map((n: any) => ({
        id: n.id,
        type: n.type || 'pipelineNode',
        position: n.position,
        data: { ...n.data, runtime: { status: 'idle' as NodeStatus } },
      }));
      const edges: Edge[] = pipeline.edges.map((e: any) => ({ ...e, type: 'smoothstep' }));
      set(state => ({
        tabs: state.tabs.map(t => t.id === state.activeTabId
          ? { ...t, name: pipeline.name, nodes, edges }
          : t),
        pipelineId: pipeline.id,
        projectId: pipeline.projectId,
        selectedIds: [],
      }));
    },

    createNewPipeline: async (name) => {
      let pid = get().projectId;
      if (!pid) {
        const { data: projects } = await api.listProjects();
        pid = projects.length > 0 ? projects[0].id : null;
        if (!pid) {
          const { data: proj } = await api.createProject({ name: 'My Projects' });
          pid = proj.id;
        }
        set({ projectId: pid });
      }
      const { data: created } = await api.createPipeline(pid!, {
        name: name || `Pipeline ${get().tabs.length + 1}`,
      });
      const newTab: Tab = {
        id: genId(),
        name: created.name,
        nodes: [],
        edges: [],
      };
      set(state => ({
        tabs: [...state.tabs, newTab],
        activeTabId: newTab.id,
        pipelineId: created.id,
        selectedIds: [],
        history: [],
        future: [],
      }));
    },
  };
});

export function useActiveTab() {
  return useStore(s => s.tabs.find(t => t.id === s.activeTabId) || s.tabs[0]);
}
