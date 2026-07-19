# FlowWeaver API Contract (Phase 7)

This document defines the backend API contract for FlowWeaver. It specifies the REST endpoints and WebSocket events used for communication between the frontend application and the backend system.

## Table of Contents
- [General Principles](#general-principles)
- [Projects](#projects)
- [Pipelines](#pipelines)
- [Executions](#executions)
- [Nodes](#nodes)
- [Plugins](#plugins)
- [Templates](#templates)

## General Principles

- All API endpoints are prefixed with `/api`.
- Request and response bodies are JSON formatted (`application/json`).
- Standard HTTP status codes are used to indicate success or failure.

### Error Format
All errors follow a standard format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided configuration is invalid.",
    "details": [
      {
        "field": "name",
        "issue": "Required field missing"
      }
    ]
  }
}
```

## Projects

### `GET /api/projects`
List all projects.

**Response (200 OK)**
```json
{
  "data": [
    {
      "id": "proj_1",
      "name": "Customer Data Processing",
      "description": "Pipelines for cleaning and normalizing customer data.",
      "createdAt": "2023-10-27T10:00:00Z",
      "updatedAt": "2023-10-27T10:00:00Z"
    }
  ],
  "meta": {
    "total": 1
  }
}
```

### `POST /api/projects`
Create a new project.

**Request**
```json
{
  "name": "Customer Data Processing",
  "description": "Pipelines for cleaning and normalizing customer data."
}
```

**Response (201 Created)**
```json
{
  "data": {
    "id": "proj_1",
    "name": "Customer Data Processing",
    "description": "Pipelines for cleaning and normalizing customer data.",
    "createdAt": "2023-10-27T10:00:00Z",
    "updatedAt": "2023-10-27T10:00:00Z"
  }
}
```

### `GET /api/projects/:id`
Get a specific project.

**Response (200 OK)**
```json
{
  "data": {
    "id": "proj_1",
    "name": "Customer Data Processing",
    "description": "Pipelines for cleaning and normalizing customer data.",
    "createdAt": "2023-10-27T10:00:00Z",
    "updatedAt": "2023-10-27T10:00:00Z"
  }
}
```
**Error (404 Not Found)**

### `PUT /api/projects/:id`
Update a project.

**Request**
```json
{
  "name": "Customer Data Pipelines",
  "description": "Updated description"
}
```

**Response (200 OK)**
```json
{
  "data": {
    "id": "proj_1",
    "name": "Customer Data Pipelines",
    "description": "Updated description",
    "createdAt": "2023-10-27T10:00:00Z",
    "updatedAt": "2023-10-27T12:00:00Z"
  }
}
```

### `DELETE /api/projects/:id`
Delete a project.

**Response (204 No Content)**

## Pipelines

### `GET /api/projects/:id/pipelines`
List pipelines in a project.

**Response (200 OK)**
```json
{
  "data": [
    {
      "id": "pipe_1",
      "projectId": "proj_1",
      "name": "Cleanse CSV",
      "createdAt": "2023-10-27T10:05:00Z",
      "updatedAt": "2023-10-27T10:05:00Z"
    }
  ]
}
```

### `POST /api/projects/:id/pipelines`
Create a new pipeline in a project.

**Request**
```json
{
  "name": "Cleanse CSV",
  "nodes": [],
  "edges": []
}
```

**Response (201 Created)**
```json
{
  "data": {
    "id": "pipe_1",
    "projectId": "proj_1",
    "name": "Cleanse CSV",
    "nodes": [],
    "edges": [],
    "createdAt": "2023-10-27T10:05:00Z",
    "updatedAt": "2023-10-27T10:05:00Z"
  }
}
```

### `GET /api/pipelines/:id`
Get a pipeline with full JSON (nodes and edges).

**Response (200 OK)**
```json
{
  "data": {
    "id": "pipe_1",
    "projectId": "proj_1",
    "name": "Cleanse CSV",
    "nodes": [
      {
        "id": "node_1",
        "type": "csv_loader",
        "position": { "x": 100, "y": 100 },
        "data": { "filePath": "/data/input.csv" }
      }
    ],
    "edges": [],
    "createdAt": "2023-10-27T10:05:00Z",
    "updatedAt": "2023-10-27T10:05:00Z"
  }
}
```

### `PUT /api/pipelines/:id`
Update a pipeline (full replace of nodes/edges).

**Request**
```json
{
  "name": "Cleanse CSV v2",
  "nodes": [...],
  "edges": [...]
}
```

**Response (200 OK)**
```json
{
  "data": {
    "id": "pipe_1",
    "projectId": "proj_1",
    "name": "Cleanse CSV v2",
    "nodes": [...],
    "edges": [...],
    "createdAt": "2023-10-27T10:05:00Z",
    "updatedAt": "2023-10-27T10:15:00Z"
  }
}
```

### `DELETE /api/pipelines/:id`
Delete a pipeline.

**Response (204 No Content)**

### `POST /api/pipelines/:id/duplicate`
Duplicate an existing pipeline.

**Response (201 Created)**
```json
{
  "data": {
    "id": "pipe_2",
    "projectId": "proj_1",
    "name": "Cleanse CSV (Copy)",
    "nodes": [...],
    "edges": [...],
    "createdAt": "2023-10-27T10:20:00Z",
    "updatedAt": "2023-10-27T10:20:00Z"
  }
}
```

## Executions

### `POST /api/pipelines/:id/execute`
Start execution of a pipeline.

**Request** (Optional parameters)
```json
{
  "variables": {
    "input_file": "/data/new_input.csv"
  }
}
```

**Response (202 Accepted)**
```json
{
  "data": {
    "executionId": "exec_1",
    "status": "pending",
    "startedAt": "2023-10-27T10:30:00Z"
  }
}
```

### `GET /api/executions/:id`
Get execution status.

**Response (200 OK)**
```json
{
  "data": {
    "id": "exec_1",
    "pipelineId": "pipe_1",
    "status": "running",
    "progress": 45,
    "startedAt": "2023-10-27T10:30:00Z",
    "completedAt": null
  }
}
```
*Status values: `pending`, `running`, `completed`, `failed`, `cancelled`.*

### `GET /api/executions/:id/logs`
Get execution logs.

**Response (200 OK)**
```json
{
  "data": [
    {
      "timestamp": "2023-10-27T10:30:01Z",
      "level": "info",
      "nodeId": "node_1",
      "message": "Started reading CSV file."
    }
  ]
}
```

### `DELETE /api/executions/:id`
Cancel an active execution.

**Response (200 OK)**
```json
{
  "data": {
    "id": "exec_1",
    "status": "cancelled"
  }
}
```

### `WS /api/executions/:id/stream`
WebSocket endpoint for live execution events.

**Events Received by Client:**

*Execution Started*
```json
{
  "type": "EXECUTION_STARTED",
  "timestamp": "2023-10-27T10:30:00Z"
}
```

*Node Status Update*
```json
{
  "type": "NODE_UPDATE",
  "nodeId": "node_1",
  "status": "running",
  "progress": 50
}
```

*Log Message*
```json
{
  "type": "LOG",
  "level": "info",
  "nodeId": "node_1",
  "message": "Processing chunk 5/10"
}
```

*Execution Completed*
```json
{
  "type": "EXECUTION_COMPLETED",
  "timestamp": "2023-10-27T10:35:00Z"
}
```

*Execution Failed*
```json
{
  "type": "EXECUTION_FAILED",
  "error": "Failed to parse CSV at line 42.",
  "timestamp": "2023-10-27T10:32:00Z"
}
```

## Nodes

### `GET /api/nodes`
List available node types.

**Response (200 OK)**
```json
{
  "data": [
    {
      "type": "csv_loader",
      "category": "Loaders",
      "label": "CSV Loader",
      "description": "Loads data from a CSV file."
    }
  ]
}
```

### `GET /api/nodes/:type`
Get detailed definition for a specific node type, including configuration schema.

**Response (200 OK)**
```json
{
  "data": {
    "type": "csv_loader",
    "category": "Loaders",
    "label": "CSV Loader",
    "description": "Loads data from a CSV file.",
    "inputs": [],
    "outputs": [{ "id": "out", "type": "dataset" }],
    "schema": {
      "type": "object",
      "properties": {
        "filePath": { "type": "string" },
        "delimiter": { "type": "string", "default": "," }
      },
      "required": ["filePath"]
    }
  }
}
```

### `POST /api/nodes/:type/validate`
Validate node configuration data against its schema.

**Request**
```json
{
  "config": {
    "filePath": "/data/test.csv"
  }
}
```

**Response (200 OK)**
```json
{
  "data": {
    "valid": true,
    "errors": []
  }
}
```

## Plugins

### `GET /api/plugins`
List installed plugins.

**Response (200 OK)**
```json
{
  "data": [
    {
      "id": "plugin_nlp_pack",
      "name": "NLP Pack",
      "version": "1.0.0",
      "author": "FlowWeaver Team",
      "nodes": ["sentiment_analysis", "entity_extraction"]
    }
  ]
}
```

### `POST /api/plugins`
Install a new plugin.

**Request**
```json
{
  "url": "https://github.com/org/plugin-repo/archive/v1.0.0.tar.gz"
}
```

**Response (202 Accepted)**
```json
{
  "data": {
    "jobId": "job_install_1",
    "status": "installing"
  }
}
```

### `DELETE /api/plugins/:id`
Uninstall a plugin.

**Response (204 No Content)**

## Templates

### `GET /api/templates`
List available pipeline templates.

**Response (200 OK)**
```json
{
  "data": [
    {
      "id": "tpl_1",
      "name": "Basic Data Cleaning",
      "description": "Loads, deduplicates, and drops nulls."
    }
  ]
}
```

### `POST /api/templates`
Create a template from an existing pipeline.

**Request**
```json
{
  "pipelineId": "pipe_1",
  "name": "My Custom Template",
  "description": "Standard processing for marketing data"
}
```

**Response (201 Created)**
```json
{
  "data": {
    "id": "tpl_2",
    "name": "My Custom Template",
    "description": "Standard processing for marketing data",
    "pipelineData": {
      "nodes": [...],
      "edges": [...]
    }
  }
}
```
