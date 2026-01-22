from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_chroma import Chroma

from rag.loader import load_pdf, load_single_pdf
from rag.splitter import split_documents
from rag.embeddings import get_embeddings
from rag.vector_store import create_vectorstore
from rag.retriever import build_api_retriever
from rag.prompt import build_messages

# -------------------- FastAPI App --------------------

app = FastAPI(title="Smart RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Paths --------------------

UPLOAD_DIR = "data/pdfs"
VECTOR_DB_DIR = "chroma_db"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------- Startup RAG Initialization --------------------

embeddings = get_embeddings()

docs = load_pdf(UPLOAD_DIR)
chunks = split_documents(docs)

if chunks:
    print(f"Initializing vectorstore with {len(chunks)} chunks")
    vectorstore = create_vectorstore(chunks, embeddings)
else:
    print("No PDFs found. Creating EMPTY vectorstore.")
    vectorstore = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings
    )

# -------- LLM --------
llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    task="text_generation",
    max_new_tokens=2000,
    temperature=0.2
)

chat_model = ChatHuggingFace(llm=llm)

# -------- Retriever --------
retriever = build_api_retriever(vectorstore)

# -------- Chat History --------
chat_history: list[tuple[str, str]] = []

# -------------------- Helpers --------------------

def should_execute(text: str) -> bool:
    return "```python" in text

def extract_code(text: str) -> str:
    return text.split("```python")[1].split("```")[0].strip()

# -------------------- Schemas --------------------

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    executable: bool
    code: str | None = None

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

    result = {
        "answer": response.content,
        "executable": False,
        "code": None
    }

    if should_execute(response.content):
        result["executable"] = True
        result["code"] = extract_code(response.content)

    chat_history.append((payload.query, response.content))

    return result

# -------------------- UPLOAD ENDPOINT --------------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save PDF
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Load & split ONLY this PDF
    docs = load_single_pdf(file_path)
    chunks = split_documents(docs)

    if not chunks:
        return {"message": "PDF uploaded but no text extracted"}

    vectorstore.add_documents(chunks)
    vectorstore.persist()

    return {
        "message": "PDF uploaded and indexed successfully",
        "filename": file.filename
    }
