"""Unit tests for app/sandbox.py.

Tests static validation logic (import blocking, exec/eval rules, file I/O)
and sandboxed execution without requiring the FastAPI server.
"""

import pytest
from app.sandbox import validate_code, execute_sandboxed


# ─── validate_code ────────────────────────────────────────────────────────────

class TestValidateCode:
    def test_safe_code_passes(self):
        code = "import requests\nprint('hello')"
        is_safe, reason = validate_code(code)
        assert is_safe is True
        assert reason is None

    def test_blocked_os_import(self):
        code = "import os\nprint(os.getcwd())"
        is_safe, reason = validate_code(code)
        assert is_safe is False
        assert "os" in reason

    def test_blocked_sys_import(self):
        code = "import sys"
        is_safe, reason = validate_code(code)
        assert is_safe is False

    def test_blocked_subprocess(self):
        code = "import subprocess"
        is_safe, reason = validate_code(code)
        assert is_safe is False

    def test_blocked_dynamic_import(self):
        code = "__import__('os').getcwd()"
        is_safe, reason = validate_code(code)
        assert is_safe is False
        assert "__import__" in reason

    def test_blocked_exec(self):
        code = "exec('print(1)')"
        is_safe, reason = validate_code(code)
        assert is_safe is False
        assert "exec" in reason

    def test_blocked_eval(self):
        code = "eval('1+1')"
        is_safe, reason = validate_code(code)
        assert is_safe is False

    def test_blocked_open(self):
        code = "open('file.txt')"
        is_safe, reason = validate_code(code)
        assert is_safe is False

    def test_from_import_blocked(self):
        code = "from socket import create_connection"
        is_safe, reason = validate_code(code)
        assert is_safe is False

    def test_safe_math(self):
        code = "import math\nprint(math.sqrt(4))"
        is_safe, _ = validate_code(code)
        assert is_safe is True


# ─── execute_sandboxed ────────────────────────────────────────────────────────

class TestExecuteSandboxed:
    def test_simple_output(self):
        result = execute_sandboxed("print('hello world')")
        assert result.blocked is False
        assert result.timed_out is False
        assert "hello world" in result.stdout

    def test_arithmetic(self):
        result = execute_sandboxed("print(2 + 2)")
        assert "4" in result.stdout

    def test_blocked_os_at_runtime(self):
        result = execute_sandboxed("import os")
        assert result.blocked is True

    def test_timeout_enforcement(self):
        result = execute_sandboxed("while True: pass", timeout=1.0)
        assert result.timed_out is True

    def test_syntax_error_captured(self):
        result = execute_sandboxed("def foo(:\n    pass")
        # Should not be blocked (syntax errors aren't import violations)
        assert result.timed_out is False
        # stderr should contain the error
        assert result.stderr != "" or result.blocked

    def test_multiline_code(self):
        code = "\n".join([
            "x = [i ** 2 for i in range(5)]",
            "print(sum(x))",
        ])
        result = execute_sandboxed(code)
        assert "30" in result.stdout
