"""Registry Service — port 10000.

A lightweight FastAPI service that allows agents to self-register and
clients to discover agent endpoints by task name.

Endpoints:
  POST /register          — register an agent
  GET  /discover/{task}   — find an agent that handles the given task
  GET  /agents            — list all registered agents
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [registry] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="A2A Registry", version="1.0.0")

# In-memory store: agent_name -> agent info dict
agents: dict[str, dict[str, Any]] = {}


class AgentRegistration(BaseModel):
    agent_name: str
    version: str = "1.0"
    description: str = ""
    tasks: list[str] = []
    endpoint: str
    tags: list[str] = []


@app.post("/register", status_code=200)
async def register(registration: AgentRegistration) -> dict:
    """Register or update an agent."""
    entry = registration.model_dump()
    entry["registered_at"] = datetime.now(timezone.utc).isoformat()
    agents[registration.agent_name] = entry
    logger.info(
        "Registered agent '%s' at %s (tasks=%s)",
        registration.agent_name,
        registration.endpoint,
        registration.tasks,
    )
    return {"status": "ok", "agent_name": registration.agent_name}


@app.get("/discover/{task}")
async def discover(task: str) -> dict:
    """Return the first agent whose task list contains *task*."""
    for agent in agents.values():
        if task in agent.get("tasks", []):
            logger.info("Discovered agent '%s' for task '%s'", agent["agent_name"], task)
            return {
                "agent_name": agent["agent_name"],
                "endpoint": agent["endpoint"],
                "description": agent.get("description", ""),
            }
    raise HTTPException(
        status_code=404,
        detail=f"No agent found for task '{task}'",
    )


@app.get("/agents")
async def list_agents() -> dict:
    """Return all registered agents."""
    return {"agents": list(agents.values())}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent_count": len(agents)}


@app.post("/api/chat")
async def chat_proxy(request: Request):
    """Proxy chat requests to the Customer Agent."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:10100/",
                headers={"X-API-Key": os.getenv("A2A_API_KEY", "secret-123")},
                json=body
            )
            return JSONResponse(status_code=response.status_code, content=response.json())
    except httpx.RequestError as e:
        logger.error("Error communicating with Customer Agent: %s", e)
        raise HTTPException(status_code=502, detail=f"Failed to connect to Customer Agent: {e}")

# Serve React App
ui_dir = os.path.join(os.path.dirname(__file__), "ui", "dist")
if os.path.isdir(ui_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(ui_dir, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        index_path = os.path.join(ui_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"error": "UI build not found. Run npm run build in registry/ui."}

if __name__ == "__main__":
    logger.info("Starting Registry on port 10000")
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")