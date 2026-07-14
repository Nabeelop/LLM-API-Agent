"""Health endpoint — system status and metadata."""

import time
from fastapi import APIRouter

from app.dependencies import get_vectorstore

router = APIRouter()

_start_time = time.time()


@router.get("/health")
async def health_check():
    """Return system health, vector store stats, and uptime."""
    vectorstore = get_vectorstore()

    try:
        doc_count = vectorstore._collection.count()
    except Exception:
        doc_count = -1

    uptime_seconds = round(time.time() - _start_time, 1)

    return {
        "status": "healthy",
        "uptime_seconds": uptime_seconds,
        "vectorstore_documents": doc_count,
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "embeddings": "BAAI/bge-small-en-v1.5",
        "sandbox": "pyodide-wasm + subprocess-isolated",
    }
