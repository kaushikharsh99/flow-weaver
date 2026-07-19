# Installation Guide

FlowWeaver requires both a Python runtime (for the compiler engine and data processing runner) and Node.js (for the React-based visual builder workspace).

---

## System Requirements

- **Operating System**: Linux, macOS, or Windows (WSL recommended).
- **Python**: Version 3.12 or newer.
- **Node.js**: Version 20 or newer (npm or pnpm).

---

## One-Click Installer

FlowWeaver includes a diagnostic installer script that verifies system dependencies, initializes Python virtual environments, installs npm packages, and seeds database migrations automatically.

Clone the repository and run:

```bash
python scripts/install.py
```

---

## Diagnostic Utility

At any point, run the system doctor script to inspect port status, check library versions, and verify database tables:

```bash
python scripts/doctor.py
```

### Typical Doctor Output:
```text
Checking Python ... ✔ OK
Checking Node.js ... ✔ OK
Checking Backend Virtual Env ... ✔ OK
Checking port 8000 (API) ... ✔ Free
Checking SQLite database ... ✔ Found
✔ FlowWeaver status: healthy! You are ready to go.
```

---

## Running Development Servers

To spin up the FastAPI backend and Vite web client concurrently:

```bash
python scripts/run.py
```

This starts:
- **Backend API Server**: http://localhost:8000
- **API Docs Portal (Swagger)**: http://localhost:8000/api/docs
- **Web UI Client Workspace**: http://localhost:8080

---

## Configuration (`.env` files)

You can customize port locations and cache settings by copying `.env.example` to `.env` in the project root:

```ini
# Backend API configuration
PORT=8000
DATABASE_URL=sqlite:///./flow_weaver.db

# Frontend settings
VITE_API_URL=http://localhost:8000/api
VITE_USE_MOCK_API=false
```
