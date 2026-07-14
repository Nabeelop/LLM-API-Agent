"""FastAPI application factory.

This is the entry point for the LLM API Agent. It assembles the modular
routers, configures CORS middleware, and adds response-time tracking.

Start with:  uvicorn app.main:app --reload --port 8000
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ask, upload, execute, health

# ─── App Factory ─────────────────────────────────────────────────────

app = FastAPI(
    title="LLM API Agent",
    description="Autonomous RAG agent for API documentation analysis and integration script generation",
    version="1.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Response-Time Middleware ────────────────────────────────────────

@app.middleware("http")
async def add_response_time_header(request: Request, call_next):
    """Track and expose request latency via X-Response-Time header."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    return response

# ─── Mount Routers ───────────────────────────────────────────────────

app.include_router(ask.router, tags=["RAG"])
app.include_router(upload.router, tags=["Ingestion"])
app.include_router(execute.router, tags=["Sandbox"])
app.include_router(health.router, tags=["System"])
