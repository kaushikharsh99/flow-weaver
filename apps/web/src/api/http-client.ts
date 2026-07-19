import { ApiClient } from './client';
import {
  ApiResponse,
  ApiListResponse,
  Project,
  PipelineSummary,
  Pipeline,
  Execution,
  ExecutionLogEntry,
  NodeTypeInfo,
  NodeTypeDetail,
  Plugin,
  Template,
  CreateProjectRequest,
  UpdateProjectRequest,
  CreatePipelineRequest,
  UpdatePipelineRequest,
  StartExecutionRequest,
  CreateTemplateRequest
} from './types';

export function createHttpClient(baseUrl: string): ApiClient {
  const fetchJson = async (url: string, options: RequestInit = {}) => {
    const res = await fetch(`${baseUrl}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    if (res.status === 204) return { data: null } as any;
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || `HTTP error ${res.status}`);
    }
    return res.json();
  };

  return {
    // Projects
    listProjects: () => fetchJson('/projects'),
    createProject: (req: CreateProjectRequest) => fetchJson('/projects', { method: 'POST', body: JSON.stringify(req) }),
    getProject: (id: string) => fetchJson(`/projects/${id}`),
    updateProject: (id: string, req: UpdateProjectRequest) => fetchJson(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(req) }),
    deleteProject: (id: string) => fetchJson(`/projects/${id}`, { method: 'DELETE' }),

    // Pipelines
    listPipelines: (projectId: string) => fetchJson(`/projects/${projectId}/pipelines`),
    createPipeline: (projectId: string, req: CreatePipelineRequest) => fetchJson(`/projects/${projectId}/pipelines`, { method: 'POST', body: JSON.stringify(req) }),
    getPipeline: (id: string) => fetchJson(`/pipelines/${id}`),
    updatePipeline: (id: string, req: UpdatePipelineRequest) => fetchJson(`/pipelines/${id}`, { method: 'PUT', body: JSON.stringify(req) }),
    deletePipeline: (id: string) => fetchJson(`/pipelines/${id}`, { method: 'DELETE' }),
    duplicatePipeline: (id: string) => fetchJson(`/pipelines/${id}/duplicate`, { method: 'POST' }),

    // Executions
    startExecution: (pipelineId: string, req?: StartExecutionRequest) => fetchJson(`/pipelines/${pipelineId}/execute`, { method: 'POST', body: JSON.stringify(req || {}) }),
    getExecution: (id: string) => fetchJson(`/executions/${id}`),
    getExecutionLogs: (id: string) => fetchJson(`/executions/${id}/logs`),
    cancelExecution: (id: string) => fetchJson(`/executions/${id}`, { method: 'DELETE' }),
    resumeExecution: (id: string) => fetchJson(`/executions/${id}/resume`, { method: 'POST' }),
    pauseExecution: (id: string) => fetchJson(`/executions/${id}/pause`, { method: 'POST' }),

    // Nodes
    listNodeTypes: () => fetchJson('/nodes'),
    getNodeType: (type: string) => fetchJson(`/nodes/${type}`),

    // Plugins
    listPlugins: () => fetchJson('/plugins'),
    installPlugin: (url: string) => fetchJson('/plugins', { method: 'POST', body: JSON.stringify({ url }) }),
    uninstallPlugin: (id: string) => fetchJson(`/plugins/${id}`, { method: 'DELETE' }),

    // Templates
    listTemplates: () => fetchJson('/templates'),
    createTemplate: (req: CreateTemplateRequest) => fetchJson('/templates', { method: 'POST', body: JSON.stringify(req) }),
  };
}
