from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import io
import traceback
from typing import List, Tuple, Optional

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_chroma import Chroma

from rag.loader import load_single_pdf
from rag.splitter import split_documents
from rag.embeddings import get_embeddings
from rag.retriever import build_api_retriever
from rag.prompt import build_messages

# -------------------- FastAPI App --------------------

app = FastAPI(title="Smart RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Paths --------------------

UPLOAD_DIR = "data/pdfs"
VECTOR_DB_DIR = "chroma_db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# -------------------- Embeddings --------------------

embeddings = get_embeddings()

# -------------------- Vectorstore (LOAD ONLY) --------------------
# IMPORTANT: Do NOT re-index on startup

vectorstore = Chroma(
    persist_directory=VECTOR_DB_DIR,
    embedding_function=embeddings
)

# -------------------- Retriever --------------------

retriever = build_api_retriever(vectorstore)

# -------------------- LLM --------------------

llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    task="text_generation",
    max_new_tokens=1500,
    temperature=0.2,
)

chat_model = ChatHuggingFace(llm=llm)

# -------------------- Chat History --------------------
# Trimmed, global (OK for dev)

MAX_HISTORY = 5
chat_history: List[Tuple[str, str]] = []

# -------------------- Helpers --------------------

def clean_response(text: str) -> str:
    """Remove DeepSeek <think> blocks"""
    if "<think>" in text:
        return text.split("</think>")[-1].strip()
    return text.strip()

import re

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

# -------------------- Schemas --------------------

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    executable: bool
    code: Optional[str] = None

class ExecuteRequest(BaseModel):
    code: str

class ExecuteResponse(BaseModel):
    output: str

# -------------------- ASK ENDPOINT --------------------

@app.post("/ask", response_model=AskResponse)
async def ask_llm(payload: AskRequest):
    retrieved_docs = retriever.invoke(payload.query)

    prompt = build_messages(
        query=payload.query,
        retrieved_docs=retrieved_docs,
        chat_history=chat_history
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

    chat_history.append((payload.query, cleaned))
    chat_history[:] = chat_history[-MAX_HISTORY:]

    return result

# -------------------- UPLOAD ENDPOINT --------------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    docs = load_single_pdf(file_path)
    chunks = split_documents(docs)

    if not chunks:
        return {"message": "PDF uploaded but no text extracted"}

    vectorstore.add_documents(chunks)   # <-- auto-persist

    return {
        "message": "PDF uploaded and indexed successfully",
        "filename": file.filename,
        "chunks_added": len(chunks)
    }

# -------------------- EXECUTE ENDPOINT --------------------

@app.post("/execute", response_model=ExecuteResponse)
async def execute_code(payload: ExecuteRequest):
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        exec_globals = {}
        exec(payload.code, exec_globals)
        output = redirected_output.getvalue()
    except Exception as e:
        output = redirected_output.getvalue() + "\n" + traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        
    return {"output": output}
