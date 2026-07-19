import type {
  ApiListResponse,
  ApiResponse,
  CreateProjectRequest,
  Project,
  UpdateProjectRequest,
  PipelineSummary,
  CreatePipelineRequest,
  Pipeline,
  UpdatePipelineRequest,
  Execution,
  StartExecutionRequest,
  ExecutionLogEntry,
  NodeTypeInfo,
  NodeTypeDetail,
  Plugin,
  Template,
  CreateTemplateRequest
} from './types';

export interface ApiClient {
  // Projects
  listProjects(): Promise<ApiListResponse<Project>>;
  createProject(req: CreateProjectRequest): Promise<ApiResponse<Project>>;
  getProject(id: string): Promise<ApiResponse<Project>>;
  updateProject(id: string, req: UpdateProjectRequest): Promise<ApiResponse<Project>>;
  deleteProject(id: string): Promise<void>;

  // Pipelines
  listPipelines(projectId: string): Promise<ApiListResponse<PipelineSummary>>;
  createPipeline(projectId: string, req: CreatePipelineRequest): Promise<ApiResponse<Pipeline>>;
  getPipeline(id: string): Promise<ApiResponse<Pipeline>>;
  updatePipeline(id: string, req: UpdatePipelineRequest): Promise<ApiResponse<Pipeline>>;
  deletePipeline(id: string): Promise<void>;
  duplicatePipeline(id: string): Promise<ApiResponse<Pipeline>>;

  // Executions
  startExecution(pipelineId: string, req?: StartExecutionRequest): Promise<ApiResponse<Execution>>;
  getExecution(id: string): Promise<ApiResponse<Execution>>;
  getExecutionLogs(id: string): Promise<ApiListResponse<ExecutionLogEntry>>;
  cancelExecution(id: string): Promise<ApiResponse<{ id: string; status: 'cancelled' }>>;
  resumeExecution(id: string): Promise<ApiResponse<{ id: string; status: 'running' }>>;
  pauseExecution(id: string): Promise<ApiResponse<{ id: string; status: 'paused' }>>;

  // Nodes
  listNodeTypes(): Promise<ApiListResponse<NodeTypeInfo>>;
  getNodeType(type: string): Promise<ApiResponse<NodeTypeDetail>>;

  // Plugins
  listPlugins(): Promise<ApiListResponse<Plugin>>;
  installPlugin(url: string): Promise<ApiResponse<{ jobId: string; status: string }>>;
  uninstallPlugin(id: string): Promise<void>;

  // Templates
  listTemplates(): Promise<ApiListResponse<Template>>;
  createTemplate(req: CreateTemplateRequest): Promise<ApiResponse<Template>>;
}
