"""Shared dependencies — singleton services used across routes.

Centralizes initialization of the vector store, retriever, LLM, and
session state so that route modules import from a single place.
"""

import os
from typing import List, Tuple

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_chroma import Chroma

from rag.embeddings import get_embeddings
from rag.retriever import build_api_retriever

# ─── Paths ───────────────────────────────────────────────────────────

UPLOAD_DIR = "data/pdfs"
VECTOR_DB_DIR = "chroma_db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# ─── Embeddings & Vector Store ───────────────────────────────────────

embeddings = get_embeddings()

vectorstore = Chroma(
    persist_directory=VECTOR_DB_DIR,
    embedding_function=embeddings,
)

# ─── Retriever ───────────────────────────────────────────────────────

retriever = build_api_retriever(vectorstore)

# ─── LLM ─────────────────────────────────────────────────────────────

llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    task="text_generation",
    max_new_tokens=800,
    temperature=0.3,
    repetition_penalty=1.3,
)

chat_model = ChatHuggingFace(llm=llm)

# ─── Session History ─────────────────────────────────────────────────

MAX_HISTORY = 5
session_histories: dict[str, List[Tuple[str, str]]] = {}


# ─── Accessor Functions ─────────────────────────────────────────────

def get_vectorstore():
    return vectorstore

def get_retriever():
    return retriever

def get_chat_model():
    return chat_model

def get_session_histories():
    return session_histories
