import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import projects, pipelines, nodes, executions, templates
from app.db import engine, Base

# Create database tables (SQLite in dev)
Base.metadata.create_all(bind=engine)

from app.engine.registry import registry
# Dynamically scan and load local developer plugins
registry.load_local_plugins("plugins")

app = FastAPI(
    title="FlowWeaver API",
    description="Backend API for FlowWeaver Visual Pipeline Builder",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify front-end domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(pipelines.router, prefix="/api", tags=["Pipelines"])
app.include_router(nodes.router, prefix="/api", tags=["Nodes"])
app.include_router(executions.router, prefix="/api", tags=["Executions"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
