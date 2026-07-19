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

import { ApiClient } from './client';

// @ts-ignore
import { NODE_TYPES, NODE_TYPE_MAP } from '../pipeline/nodeTypes';

const delay = (ms = 80) => new Promise(resolve => setTimeout(resolve, ms));
const genId = (prefix: string) => `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
const now = () => new Date().toISOString();

export function createMockClient(): ApiClient {
  const projects = new Map<string, Project>();
  const pipelines = new Map<string, Pipeline>();
  const executions = new Map<string, Execution>();
  const executionLogs = new Map<string, ExecutionLogEntry[]>();
  const templates = new Map<string, Template>();
  const plugins = new Map<string, Plugin>();

  // Seed default data
  const defaultProjectId = 'proj_default';
  projects.set(defaultProjectId, {
    id: defaultProjectId,
    name: 'My Projects',
    description: 'Default project',
    createdAt: now(),
    updatedAt: now(),
  });

  const defaultPipelineId = 'pipe_default';
  pipelines.set(defaultPipelineId, {
    id: defaultPipelineId,
    projectId: defaultProjectId,
    name: 'My Pipeline',
    description: 'Default empty pipeline',
    nodes: [],
    edges: [],
    createdAt: now(),
    updatedAt: now(),
  });

  return {
    async listProjects() {
      await delay();
      const data = Array.from(projects.values());
      return { data, meta: { total: data.length } };
    },

    async createProject(req: CreateProjectRequest) {
      await delay();
      const id = genId('proj');
      const project: Project = {
        id,
        name: req.name,
        description: req.description || '',
        createdAt: now(),
        updatedAt: now(),
      };
      projects.set(id, project);
      return { data: project };
    },

    async getProject(id: string) {
      await delay();
      const project = projects.get(id);
      if (!project) throw new Error(`Project not found: ${id}`);
      return { data: project };
    },

    async updateProject(id: string, req: UpdateProjectRequest) {
      await delay();
      const project = projects.get(id);
      if (!project) throw new Error(`Project not found: ${id}`);
      
      const updated: Project = {
        ...project,
        ...req,
        updatedAt: now(),
      };
      projects.set(id, updated);
      return { data: updated };
    },

    async deleteProject(id: string) {
      await delay();
      if (!projects.has(id)) throw new Error(`Project not found: ${id}`);
      projects.delete(id);
      
      // Delete associated pipelines
      for (const [pId, p] of pipelines.entries()) {
        if (p.projectId === id) pipelines.delete(pId);
      }
    },

    async listPipelines(projectId: string) {
      await delay();
      const data: PipelineSummary[] = Array.from(pipelines.values())
        .filter(p => p.projectId === projectId)
        .map(({ id, projectId: pId, name, description, createdAt, updatedAt }) => ({
          id, projectId: pId, name, description, createdAt, updatedAt
        }));
      return { data, meta: { total: data.length } };
    },

    async createPipeline(projectId: string, req: CreatePipelineRequest) {
      await delay();
      const id = genId('pipe');
      const pipeline: Pipeline = {
        id,
        projectId,
        name: req.name,
        description: req.description,
        nodes: [],
        edges: [],
        createdAt: now(),
        updatedAt: now(),
      };
      pipelines.set(id, pipeline);
      return { data: pipeline };
    },

    async getPipeline(id: string) {
      await delay();
      const pipeline = pipelines.get(id);
      if (!pipeline) throw new Error(`Pipeline not found: ${id}`);
      return { data: pipeline };
    },

    async updatePipeline(id: string, req: UpdatePipelineRequest) {
      await delay();
      const pipeline = pipelines.get(id);
      if (!pipeline) throw new Error(`Pipeline not found: ${id}`);
      
      const updated: Pipeline = {
        ...pipeline,
        ...req,
        updatedAt: now(),
      };
      pipelines.set(id, updated);
      return { data: updated };
    },

    async deletePipeline(id: string) {
      await delay();
      if (!pipelines.has(id)) throw new Error(`Pipeline not found: ${id}`);
      pipelines.delete(id);
    },

    async duplicatePipeline(id: string) {
      await delay();
      const pipeline = pipelines.get(id);
      if (!pipeline) throw new Error(`Pipeline not found: ${id}`);
      
      const newId = genId('pipe');
      const duplicated: Pipeline = {
        ...pipeline,
        id: newId,
        name: `${pipeline.name} (Copy)`,
        createdAt: now(),
        updatedAt: now(),
      };
      pipelines.set(newId, duplicated);
      return { data: duplicated };
    },

    async startExecution(pipelineId: string, req?: StartExecutionRequest) {
      await delay();
      const id = genId('exec');
      const execution: Execution = {
        id,
        pipelineId,
        status: 'pending',
        progress: 0,
        startedAt: now(),
        completedAt: null,
      };
      executions.set(id, execution);
      return { data: execution };
    },

    async getExecution(id: string) {
      await delay();
      const execution = executions.get(id);
      if (!execution) throw new Error(`Execution not found: ${id}`);
      return { data: execution };
    },

    async getExecutionLogs(id: string) {
      await delay();
      const logs = executionLogs.get(id) || [];
      return { data: logs, meta: { total: logs.length } };
    },

    async cancelExecution(id: string) {
      await delay();
      const execution = executions.get(id);
      if (!execution) throw new Error(`Execution not found: ${id}`);
      
      execution.status = 'cancelled';
      executions.set(id, execution);
      return { data: { id, status: 'cancelled' } };
    },

    async listNodeTypes() {
      await delay();
      // Ensure we extract only NodeTypeInfo properties
      const data: NodeTypeInfo[] = (NODE_TYPES || []).map((nt: any) => ({
        type: nt.type,
        category: nt.category,
        label: nt.label,
        description: nt.description,
      }));
      return { data, meta: { total: data.length } };
    },

    async getNodeType(type: string) {
      await delay();
      const nt = (NODE_TYPE_MAP || {})[type];
      if (!nt) throw new Error(`Node type not found: ${type}`);
      return {
        data: {
          type: nt.id,
          category: nt.category,
          label: nt.label,
          description: nt.description,
          inputs: nt.inputs,
          outputs: nt.outputs,
          parameters: nt.paramsSchema
        } as NodeTypeDetail
      };
    },

    async listPlugins() {
      await delay();
      const data = Array.from(plugins.values());
      return { data, meta: { total: data.length } };
    },

    async installPlugin(url: string) {
      await delay(500); // slightly longer simulated delay for installation
      return { data: { jobId: genId('job'), status: 'completed' } };
    },

    async uninstallPlugin(id: string) {
      await delay();
      plugins.delete(id);
    },

    async listTemplates() {
      await delay();
      const data = Array.from(templates.values());
      return { data, meta: { total: data.length } };
    },

    async createTemplate(req: CreateTemplateRequest) {
      await delay();
      const id = genId('tpl');
      const pipeline = pipelines.get(req.pipelineId);
      const pipelineData = pipeline ? { nodes: pipeline.nodes, edges: pipeline.edges } : undefined;
      const template: Template = {
        id,
        name: req.name,
        description: req.description || '',
        pipelineData,
      };
      templates.set(id, template);
      return { data: template };
    },
  };
}
