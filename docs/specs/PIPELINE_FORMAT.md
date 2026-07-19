# Phase 3 Pipeline Format Specification

## Overview

This document defines the official v1.0.0 JSON schema for FlowWeaver pipelines. The pipeline format serves as the core contract for serialization, sharing, executing, and rendering workflows within the FlowWeaver ecosystem.

As the platform evolves, backwards compatibility and schema stability are paramount. This specification outlines the expected structure, metadata, variables, visual state, and graph topology.

## Core Principles

1.  **Strict Typing**: Every property has a precise type definition.
2.  **Backwards Compatibility**: The `version` field dictates parsing logic. Future versions must provide migration paths.
3.  **Visual vs. Logical Separation**: Node positions, sizes, and colors are preserved alongside execution parameters.
4.  **Extensibility**: The schema supports custom parameters and future capabilities via structured metadata blocks.

## Schema Versioning

FlowWeaver uses semantic versioning (`MAJOR.MINOR.PATCH`) for the pipeline format.
- **MAJOR**: Breaking changes to the schema structure (e.g., changing how edges reference handles).
- **MINOR**: Additions of new optional fields or capabilities (e.g., adding pipeline `variables`).
- **PATCH**: Bug fixes in schema constraints or documentation updates.

---

## v1.0.0 JSON Schema

Below is the conceptual JSON Schema definition for a FlowWeaver Pipeline. The canonical URL for this schema is `https://flowweaver.dev/schemas/pipeline/v1.json`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://flowweaver.dev/schemas/pipeline/v1.json",
  "title": "FlowWeaver Pipeline",
  "description": "A visual pipeline definition for FlowWeaver.",
  "type": "object",
  "required": ["$schema", "version", "id", "name", "nodes", "edges"],
  "properties": {
    "$schema": {
      "type": "string",
      "description": "URI of the JSON Schema used to validate this document."
    },
    "version": {
      "type": "string",
      "description": "Semantic version of the pipeline format.",
      "enum": ["1.0.0"]
    },
    "id": {
      "type": "string",
      "description": "Unique identifier (UUID) for the pipeline."
    },
    "name": {
      "type": "string",
      "description": "Human-readable name of the pipeline."
    },
    "description": {
      "type": "string",
      "description": "Optional description of what the pipeline does."
    },
    "author": {
      "type": "string",
      "description": "Optional author name or identifier."
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of creation."
    },
    "updatedAt": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of last modification."
    },
    "variables": {
      "type": "object",
      "description": "Pipeline-level variables that can be referenced in node parameters.",
      "additionalProperties": {
        "type": ["string", "number", "boolean", "null"]
      }
    },
    "settings": {
      "type": "object",
      "description": "Global execution settings for the pipeline.",
      "properties": {
        "maxConcurrency": { "type": "integer", "minimum": 1 },
        "timeoutMs": { "type": "integer", "minimum": 0 }
      },
      "additionalProperties": true
    },
    "viewport": {
      "type": "object",
      "description": "React Flow viewport state.",
      "required": ["x", "y", "zoom"],
      "properties": {
        "x": { "type": "number" },
        "y": { "type": "number" },
        "zoom": { "type": "number", "minimum": 0 }
      }
    },
    "nodes": {
      "type": "array",
      "description": "List of all nodes in the pipeline.",
      "items": {
        "$ref": "#/definitions/Node"
      }
    },
    "edges": {
      "type": "array",
      "description": "List of all edges connecting nodes.",
      "items": {
        "$ref": "#/definitions/Edge"
      }
    }
  },
  "definitions": {
    "Node": {
      "type": "object",
      "required": ["id", "type", "position", "data"],
      "properties": {
        "id": { "type": "string", "description": "Unique identifier for the node." },
        "type": { 
          "type": "string", 
          "enum": ["pipelineNode", "commentNode"],
          "description": "The React Flow node type." 
        },
        "position": {
          "type": "object",
          "required": ["x", "y"],
          "properties": {
            "x": { "type": "number" },
            "y": { "type": "number" }
          }
        },
        "data": {
          "type": "object",
          "required": ["typeId"],
          "properties": {
            "typeId": { "type": "string", "description": "Registry ID for execution logic (e.g., 'load_csv')." },
            "title": { "type": "string", "description": "Display title for the node." },
            "params": { 
              "type": "object", 
              "description": "Execution parameters specific to the node type.",
              "additionalProperties": true 
            },
            "collapsed": { "type": "boolean", "default": false },
            "disabled": { "type": "boolean", "default": false, "description": "If true, bypass this node during execution." },
            "colorLabel": { "type": "string", "description": "Hex color code for visual grouping." },
            "comment": { "type": "string", "description": "Text content for commentNode types." },
            "width": { "type": "number" },
            "height": { "type": "number" }
          },
          "additionalProperties": true
        }
      }
    },
    "Edge": {
      "type": "object",
      "required": ["id", "source", "target", "sourceHandle", "targetHandle"],
      "properties": {
        "id": { "type": "string", "description": "Unique identifier for the edge." },
        "source": { "type": "string", "description": "ID of the source node." },
        "target": { "type": "string", "description": "ID of the target node." },
        "sourceHandle": { "type": "string", "description": "ID of the output handle on the source node." },
        "targetHandle": { "type": "string", "description": "ID of the input handle on the target node." }
      }
    }
  }
}
```

## Field Documentation

### Root Properties

| Field | Type | Required | Description |
|---|---|---|---|
| `$schema` | String | Yes | Reference to the JSON schema validation URL. |
| `version` | String | Yes | Semver string of the format (e.g., `1.0.0`). |
| `id` | String | Yes | Unique UUIDv4 representing the pipeline. |
| `name` | String | Yes | Display name of the pipeline. |
| `description` | String | No | Detailed explanation of the pipeline's purpose. |
| `author` | String | No | Identifier of the creator (email, username, etc.). |
| `createdAt` | String | No | ISO 8601 Datetime string. |
| `updatedAt` | String | No | ISO 8601 Datetime string. |
| `variables` | Object | No | Key-value pairs for global variables (e.g., API keys, base paths). |
| `settings` | Object | No | Global pipeline execution settings (concurrency, timeouts). |
| `viewport` | Object | No | X, Y, and Zoom state for the React Flow canvas to resume editing state. |
| `nodes` | Array | Yes | Array of node objects representing logic and comments. |
| `edges` | Array | Yes | Array of edge objects representing data flow. |

### Node Data Properties (`node.data`)

| Field | Type | Required | Description |
|---|---|---|---|
| `typeId` | String | Yes | The internal registry ID for the node logic (e.g., `load_csv`, `filter_rows`). |
| `title` | String | No | Custom title overrides. Defaults to registry title if omitted. |
| `params` | Object | No | Key-value dictionary of the user's configured settings for the node. |
| `collapsed` | Boolean | No | Whether the node's UI is minimized on the canvas. |
| `disabled` | Boolean | No | If true, the execution engine skips or passes through this node. |
| `colorLabel` | String | No | Visual accent color (hex format, e.g., `#ff0000`). |
| `comment` | String | No | The markdown/text content if the node is a `commentNode`. |
| `width` | Number | No | Explicit width set by user resizing. |
| `height` | Number | No | Explicit height set by user resizing. |

---

## Example Pipeline

```json
{
  "$schema": "https://flowweaver.dev/schemas/pipeline/v1.json",
  "version": "1.0.0",
  "id": "e4f8a9d1-3b4c-4a2e-8c7a-9b1d3f5e6a7c",
  "name": "Customer Data Processing",
  "description": "Loads customer data, filters out inactive users, and exports to JSON.",
  "author": "jane.doe@example.com",
  "createdAt": "2024-03-15T10:30:00Z",
  "updatedAt": "2024-03-15T11:45:00Z",
  "variables": {
    "BASE_DIR": "/data/prod",
    "ENABLE_DEBUG": false
  },
  "settings": {
    "maxConcurrency": 4
  },
  "viewport": {
    "x": -50,
    "y": -20,
    "zoom": 1.2
  },
  "nodes": [
    {
      "id": "node-1",
      "type": "pipelineNode",
      "position": { "x": 100, "y": 200 },
      "data": {
        "typeId": "load_csv",
        "title": "Load Customers",
        "params": { 
          "path": "${BASE_DIR}/customers.csv", 
          "delimiter": ",", 
          "header": true 
        },
        "colorLabel": "#3b82f6"
      }
    },
    {
      "id": "node-2",
      "type": "pipelineNode",
      "position": { "x": 400, "y": 200 },
      "data": {
        "typeId": "filter_rows",
        "title": "Filter Active",
        "params": { 
          "condition": "status == 'active'" 
        }
      }
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "node-1",
      "target": "node-2",
      "sourceHandle": "out",
      "targetHandle": "in"
    }
  ]
}
```

## Migration Strategy

As FlowWeaver evolves, future updates to the platform that bump the format version must provide a migration script.

### Process
1. **Detection**: Upon loading a `.json` pipeline file, the system checks the `version` field.
2. **Migration Registry**: The application maintains a registry of migrations (e.g., `migrateV1ToV2(pipeline)`).
3. **Sequential Upgrade**: If a user loads a `v1.0.0` pipeline into a `v3.0.0` compatible platform, the pipeline runs through `migrateV1ToV2` -> `migrateV2ToV3`.
4. **Validation**: Post-migration, the JSON is validated against the latest JSON Schema. If validation passes, the pipeline mounts in the store. If it fails, an explicit schema error is surfaced to the user.

### Guidelines for Plugin Authors
- Never change the shape of `params` in a breaking way for existing nodes.
- If a parameter's meaning must change, deprecate the old parameter (keep it functional but hidden in UI) and introduce a new parameter.
- The core framework manages schema migrations for `nodes`, `edges`, `variables`, etc. Plugin authors are responsible for backwards compatibility of their `typeId`'s `params`.
