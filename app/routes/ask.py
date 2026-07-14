"""Ask endpoint — RAG-powered question answering with code extraction."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_retriever, get_chat_model, get_session_histories, MAX_HISTORY
from rag.prompt import build_messages

import re

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"

class AskResponse(BaseModel):
    answer: str
    executable: bool
    code: Optional[str] = None


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


def extract_code(text: str) -> Optional[str]:
    if "<EXECUTE_PYTHON>" in text and "</EXECUTE_PYTHON>" in text:
        try:
            return text.split("<EXECUTE_PYTHON>")[1].split("</EXECUTE_PYTHON>")[0].strip()
        except IndexError:
            pass
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


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

    result = {
        "answer": cleaned,
        "executable": False,
        "code": None
    }

    if should_execute(cleaned):
        code = extract_code(cleaned)
        if code:
            result["executable"] = True
            result["code"] = code

    history.append((payload.query, cleaned))
    session_histories[session_id] = history[-MAX_HISTORY:]

    return result
