# FlowWeaver Documentation Portal

Welcome to the official FlowWeaver documentation. FlowWeaver is an open-source visual dataset preprocessing platform designed for AI and Machine Learning researchers to clean, filter, tokenize, and restructure datasets with ease.

---

## Document Index

### 🚀 Getting Started & Installation
- [Getting Started](getting-started.md) — Core concepts, visual interface introduction, and your first workflow.
- [Installation Guide](installation.md) — Running FlowWeaver locally, managing python virtual environments, and configuration.

### 🏛 Architecture & Design
- [System Architecture](design/ARCHITECTURE.md) — The 7-layer design system, compilation stages, and database models.
- [Pipeline Format Spec](specs/PIPELINE_FORMAT.md) — The v1.0.0 Pipeline JSON Schema spec.
- [Node Specification](specs/NODE_SPEC.md) — Detailed contract details for custom node developers.

### 💻 Developer SDK & Reference
- [SDK Reference](sdk-reference.md) — Complete python SDK class and decorator parameters.
- [Creating Nodes](creating-nodes.md) — How to scaffold, adapt, and code custom nodes.
- [Plugin Development](plugin-development.md) — Scaffolding plugins, packaging, and publishing.
- [CLI Reference](cli-reference.md) — Guide to the `flowweaver` CLI developer tool suite.

### 📖 Workflows, Examples & Tutorials
- [Preprocessing Examples](examples.md) — Walkthrough of the 6 default pipeline templates.
- [Tutorial: Fine-Tuning Clean-up](tutorials.md) — End-to-end tutorial preprocessing a raw dataset for Llama 3 training.
- [Frequently Asked Questions (FAQ)](faq.md) — Common trouble spots, running in sandboxes, and troubleshooting.

---

## Core Philosophy

FlowWeaver separates interface definitions from core algorithms:
> **"Nodes are adapters. Business logic belongs in reusable modules."**

Refer to the [Contributing & Style Guide](CONTRIBUTING.md) for strict rules regarding node line limits, sandboxing, and test requirements.
