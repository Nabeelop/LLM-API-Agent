"""Execute endpoint — secure sandboxed code execution."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.sandbox import execute_sandboxed

router = APIRouter()


class ExecuteRequest(BaseModel):
    code: str

class ExecuteResponse(BaseModel):
    output: str
    blocked: bool = False
    blocked_reason: str | None = None


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(payload: ExecuteRequest):
    """Execute Python code inside the secure sandbox.

    The sandbox enforces:
    - AST-based import validation (blocks os, subprocess, socket, etc.)
    - CPU timeout (5 seconds)
    - Sanitized environment (no API tokens leaked)
    - Temp directory isolation
    """
    result = execute_sandboxed(payload.code)

    output = result.stdout
    if result.stderr:
        output += "\n" + result.stderr if output else result.stderr

    return {
        "output": output.strip() or "(No output)",
        "blocked": result.blocked,
        "blocked_reason": result.blocked_reason,
    }
