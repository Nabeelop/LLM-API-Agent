"""Upload endpoint — PDF ingestion and vector store indexing."""

import os
import hashlib
import asyncio
from fastapi import APIRouter, UploadFile, File

from app.dependencies import get_vectorstore, UPLOAD_DIR, rebuild_retriever
from rag.loader import load_single_pdf
from rag.splitter import split_documents

router = APIRouter()


def _process_pdf(file_path: str, filename: str, vectorstore):
    """Load, split, deduplicate, and index a PDF (runs in thread pool)."""
    docs = load_single_pdf(file_path)
    chunks = split_documents(docs)

    if not chunks:
        return {"message": "PDF uploaded but no text extracted", "chunks_added": 0}

    # Generate deterministic IDs to prevent duplicate indexing
    ids = []
    for chunk in chunks:
        source = chunk.metadata.get("source", filename)
        content = chunk.page_content
        unique_str = f"{source}_{content}"
        chunk_id = hashlib.md5(unique_str.encode("utf-8")).hexdigest()
        ids.append(chunk_id)

    vectorstore.add_documents(chunks, ids=ids)

    # Rebuild the live retriever singleton so subsequent /ask queries
    # immediately see the newly indexed documents.
    rebuild_retriever()

    return {
        "message": "PDF uploaded and indexed successfully",
        "filename": filename,
        "chunks_added": len(chunks),
    }


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    vectorstore = get_vectorstore()

    # Run PDF processing in a background thread for non-blocking I/O
    result = await asyncio.to_thread(_process_pdf, file_path, file.filename, vectorstore)

    return result
