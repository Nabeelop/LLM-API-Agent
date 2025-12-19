from typing import List
from langchain_core.documents import Document


def build_messages(
    query: str,
    retrieved_docs: List[Document],
    chat_history: List[str],
) -> str:
    """
    Builds a single plain-text prompt.
    No SystemMessage / HumanMessage / AIMessage.
    """

    # ---- Context from retrieved docs ----
    context = "\n\n".join(
        f"[DOC {i+1}]\n{doc.page_content}"
        for i, doc in enumerate(retrieved_docs)
    )

    # ---- Chat history (plain text) ----
    history = "\n".join(chat_history[-6:]) if chat_history else "None"

    prompt = f"""
You are an expert API documentation assistant.

Your task:
- Answer strictly using the provided API documentation
- Prefer executable examples (curl / Python / JS)
- Mention HTTP method, endpoint, headers, auth if applicable
- If information is missing, say: "Not found in documentation"

Chat History:
{history}

API Documentation:
{context}

User Question:
{query}

Answer clearly and concisely:
"""

    return prompt.strip()
