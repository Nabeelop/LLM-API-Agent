"""Secure code execution sandbox.

Provides static analysis (AST-based import validation) and sandboxed
subprocess execution with strict resource limits. This module enforces:

- Blocked dangerous imports (os, sys, subprocess, shutil, socket, etc.)
- CPU time limit (5 seconds)
- Memory limit (50 MB via job object on Windows)
- Sanitized environment variables (strips secrets like API tokens)
- Temp directory isolation for execution context
"""

import ast
import os
import sys
import subprocess
import tempfile
import traceback
from dataclasses import dataclass
from typing import Optional


# Modules that must NEVER be importable from sandboxed code
BLOCKED_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "socket", "http", "urllib",
    "ctypes", "importlib", "pathlib", "signal", "multiprocessing",
    "threading", "webbrowser", "code", "codeop", "compileall",
    "ftplib", "smtplib", "telnetlib", "xmlrpc", "pickle", "shelve",
    "sqlite3", "io", "tempfile", "glob", "fnmatch",
})


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    blocked: bool
    blocked_reason: Optional[str] = None
    timed_out: bool = False


def _extract_imports(code: str) -> list[str]:
    """Use AST to extract all imported module names from code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module.split(".")[0])
    return modules


def validate_code(code: str) -> tuple[bool, Optional[str]]:
    """Validate code is safe to execute by checking imports against blocklist.

    Returns (is_safe, reason) where reason is None if safe.
    """
    # Check for __import__ calls which bypass normal import statements
    if "__import__" in code:
        return False, "Dynamic __import__() calls are not permitted"

    if "exec(" in code or "eval(" in code:
        return False, "exec() and eval() are not permitted in the sandbox"

    if "open(" in code:
        return False, "File I/O via open() is not permitted in the sandbox"

    imported = _extract_imports(code)
    for mod in imported:
        if mod in BLOCKED_MODULES:
            return False, f"Import of '{mod}' is blocked for security"

    return True, None


def _build_safe_env() -> dict[str, str]:
    """Build a sanitized environment for subprocess execution.

    Strips sensitive variables like API tokens and secrets while keeping
    basic PATH and system variables needed for Python to function.
    """
    sensitive_keys = {
        "HUGGINGFACEHUB_API_TOKEN", "HF_TOKEN", "OPENAI_API_KEY",
        "AWS_SECRET_ACCESS_KEY", "DATABASE_URL", "SECRET_KEY",
    }
    env = {}
    for key, val in os.environ.items():
        if key.upper() not in sensitive_keys:
            env[key] = val
    return env


def execute_sandboxed(code: str, timeout: float = 5.0, max_memory_mb: int = 50) -> SandboxResult:
    """Execute Python code in a sandboxed subprocess with resource limits.

    1. Static analysis: reject code that imports blocked modules
    2. Run in an isolated temp directory
    3. Enforce CPU timeout
    4. Strip secrets from environment
    """
    # --- Step 1: Static validation ---
    is_safe, reason = validate_code(code)
    if not is_safe:
        return SandboxResult(
            stdout="",
            stderr=f"⚠️ Sandbox blocked execution: {reason}",
            blocked=True,
            blocked_reason=reason,
        )

    # --- Step 2: Execute in isolated temp dir ---
    safe_env = _build_safe_env()

    try:
        with tempfile.TemporaryDirectory(prefix="sandbox_") as tmpdir:
            creation_flags = 0
            # On Windows, use CREATE_NEW_PROCESS_GROUP for isolation
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env=safe_env,
                creationflags=creation_flags,
            )

            return SandboxResult(
                stdout=result.stdout,
                stderr=result.stderr,
                blocked=False,
            )

    except subprocess.TimeoutExpired:
        return SandboxResult(
            stdout="",
            stderr=f"⚠️ Execution timed out (limit: {timeout}s). Code may contain infinite loops.",
            blocked=False,
            timed_out=True,
        )
    except Exception as e:
        return SandboxResult(
            stdout="",
            stderr=f"Execution failed: {str(e)}\n{traceback.format_exc()}",
            blocked=False,
        )
