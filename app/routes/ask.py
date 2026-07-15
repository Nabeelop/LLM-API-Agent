"""Ask endpoint — RAG-powered question answering with code extraction."""

import re
import textwrap
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_retriever, get_chat_model, get_session_histories, MAX_HISTORY
from app.session_store import save_sessions
from rag.prompt import build_messages
from app.sandbox import execute_sandboxed
from langchain_core.messages import AIMessage, HumanMessage

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"

class AskResponse(BaseModel):
    answer: str
    executable: bool
    code: Optional[str] = None
    attempts: Optional[list] = None


# ─── Helpers ─────────────────────────────────────────────────────────

def truncate_repetition(text: str, min_len: int = 20, max_repeats: int = 3) -> str:
    """Detect and truncate repetitive looping text."""
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    seen: dict[str, int] = {}
    result = []
    for sentence in sentences:
        key = sentence.strip().lower()
        if len(key) < min_len:
            result.append(sentence)
            continue
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > max_repeats:
            break
        result.append(sentence)
    return " ".join(result).strip()


def clean_response(text: str) -> str:
    """Remove DeepSeek <think> blocks and truncate repetitive output."""
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    elif "<think>" in text:
        text = text.split("<think>")[0].strip()
    text = text.strip()
    text = truncate_repetition(text)
    return text


def should_execute(text: str) -> bool:
    return ("<EXECUTE_PYTHON>" in text and "</EXECUTE_PYTHON>" in text) or ("```python" in text)


def _fix_missing_indentation(code: str) -> str:
    """Fix code where the LLM forgot to indent blocks after colons.

    Checks line-by-line: if the previous non-empty line ends with ':' and the
    current line is not more indented, it forces a relative 4-space indentation.
    """
    try:
        compile(code, "<sandbox>", "exec")
        return code  # Code is valid, don't touch it
    except SyntaxError:
        pass  # Needs fixing

    lines = code.split("\n")
    fixed = []
    prev_colon_indent = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed.append("")
            continue

        current_indent = len(line) - len(line.lstrip())

        if prev_colon_indent is not None:
            # If the current line is not more indented than the colon line, force indent it!
            if current_indent <= prev_colon_indent:
                line = " " * (prev_colon_indent + 4) + stripped
                current_indent = prev_colon_indent + 4
            prev_colon_indent = None  # Reset

        fixed.append(line)

        # Record if this line opens a new block
        if stripped.endswith(":") and not stripped.startswith("#"):
            prev_colon_indent = current_indent

    result = "\n".join(fixed)

    # Verify the fix actually helped
    try:
        compile(result, "<sandbox>", "exec")
        return result
    except SyntaxError:
        # If nuestro fix didn't help, return original
        return code


def extract_code(text: str) -> Optional[str]:
    """Extract code from the last <EXECUTE_PYTHON> tag or ```python block, then fix indentation."""
    raw = None
    if "<EXECUTE_PYTHON>" in text and "</EXECUTE_PYTHON>" in text:
        parts = text.split("<EXECUTE_PYTHON>")
        last_part = parts[-1]
        if "</EXECUTE_PYTHON>" in last_part:
            raw = last_part.split("</EXECUTE_PYTHON>")[0]
            
    if raw is None:
        parts = text.split("```python")
        last_part = parts[-1]
        if "```" in last_part:
            raw = last_part.split("```")[0]
            
    if raw is None:
        return None
        
    # Dedent, strip, then auto-fix missing indentation
    code = textwrap.dedent(raw).strip()
    code = _fix_missing_indentation(code)
    return code


def strip_code_blocks(text: str) -> str:
    """Remove code blocks from the answer so the chat shows only the description."""
    # Remove <EXECUTE_PYTHON>...</EXECUTE_PYTHON> blocks
    text = re.sub(
        r"<EXECUTE_PYTHON>.*?</EXECUTE_PYTHON>",
        "\n*(Code sent to sandbox)*\n",
        text,
        flags=re.DOTALL,
    )
    # Remove ```python...``` blocks
    text = re.sub(
        r"```python\n.*?\n```",
        "\n*(Code sent to sandbox)*\n",
        text,
        flags=re.DOTALL,
    )
    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ─── Endpoint ────────────────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
async def ask_llm(payload: AskRequest):
    retriever = get_retriever()
    chat_model = get_chat_model()
    session_histories = get_session_histories()

    retrieved_docs = retriever.invoke(payload.query)

    session_id = payload.session_id or "default"
    if session_id not in session_histories:
        session_histories[session_id] = []

    history = session_histories[session_id]

    prompt = build_messages(
        query=payload.query,
        retrieved_docs=retrieved_docs,
        chat_history=history
    )

    response = chat_model.invoke(prompt)
    cleaned = clean_response(response.content)

    code = None
    executable = False
    attempts_log = []

    if should_execute(cleaned):
        code = extract_code(cleaned)
        if code:
            executable = True
            
            # Autonomous self-correcting feedback loop
            max_attempts = 3
            current_attempt = 0
            current_code = code
            current_response_text = cleaned
            
            messages_context = list(prompt)
            
            while current_attempt < max_attempts:
                current_attempt += 1
                result = execute_sandboxed(current_code)
                
                attempt_entry = {
                    "attempt": current_attempt,
                    "code": current_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "blocked": result.blocked,
                    "blocked_reason": result.blocked_reason,
                    "timed_out": result.timed_out
                }
                attempts_log.append(attempt_entry)
                
                # Check for compilation or runtime errors
                has_error = False
                error_msg = ""
                
                if result.blocked:
                    has_error = True
                    error_msg = f"Security block: {result.blocked_reason}"
                elif result.timed_out:
                    has_error = True
                    error_msg = "Execution timed out (limit: 5.0 seconds). Script may contain infinite loops."
                elif result.stderr and ("Traceback" in result.stderr or "Error:" in result.stderr or "Exception:" in result.stderr or "SyntaxError:" in result.stderr or "IndentationError:" in result.stderr):
                    has_error = True
                    error_msg = result.stderr.strip()
                elif result.stderr and result.stderr.strip():
                    # Check if it looks like actual errors and not warnings
                    stderr_lower = result.stderr.lower()
                    if "warning" not in stderr_lower and "info" not in stderr_lower:
                        has_error = True
                        error_msg = result.stderr.strip()
                
                if not has_error:
                    # Successful run! Lock: update code and return
                    code = current_code
                    cleaned = current_response_text
                    break
                else:
                    # If we failed but have remaining retries, feed the traceback back to the LLM
                    if current_attempt < max_attempts:
                        messages_context.append(AIMessage(content=current_response_text))
                        
                        feedback_prompt = (
                            f"The code generated in your previous response failed execution in the secure sandbox with the following issue:\n"
                            f"```\n{error_msg}\n```\n\n"
                            f"Stdout (if any):\n"
                            f"```\n{result.stdout}\n```\n\n"
                            f"Please read the error message carefullly, fix any syntax, compile, indentation (e.g. missing 4-space indent under try/except/if declarations), or package/security issues, and output the entire corrected script inside <EXECUTE_PYTHON>...</EXECUTE_PYTHON> tags."
                        )
                        messages_context.append(HumanMessage(content=feedback_prompt))
                        
                        # Re-run LLM query
                        retry_response = chat_model.invoke(messages_context)
                        current_response_text = clean_response(retry_response.content)
                        new_code = extract_code(current_response_text)
                        if new_code:
                            current_code = new_code
                    else:
                        # Max retries reached without success, return the last generated state
                        code = current_code
                        cleaned = current_response_text

    # Strip code blocks from the displayed answer so chat shows only the description
    display_answer = strip_code_blocks(cleaned) if executable else cleaned

    # Append custom verification status message in the chat
    if executable and attempts_log:
        last_attempt = attempts_log[-1]
        success = not (last_attempt["blocked"] or last_attempt["timed_out"] or (last_attempt["stderr"] and ("Traceback" in last_attempt["stderr"] or "Error:" in last_attempt["stderr"] or "Exception:" in last_attempt["stderr"])))
        
        if success:
            if len(attempts_log) == 1:
                display_answer += "\n\n*(Code verified and ran successfully in isolated sandbox)*"
            else:
                display_answer += f"\n\n*(Autonomous Agent Self-Corrected and verified code successfully in sandbox after {len(attempts_log)} attempts)*"
        else:
            display_answer += f"\n\n*(Autonomous Agent ran code but failed to resolve error in sandbox after {len(attempts_log)} attempts)*"

    history.append((payload.query, cleaned))
    session_histories[session_id] = history[-MAX_HISTORY:]
    save_sessions()  # Flush to disk so history survives restarts

    return {
        "answer": display_answer,
        "executable": executable,
        "code": code,
        "attempts": attempts_log if executable else None
    }
