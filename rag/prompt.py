from langchain.messages import SystemMessage, HumanMessage, AIMessage


SYSTEM_PROMPT = """
You are an expert Smart API Assistant.

Rules:
- Answer ONLY using the provided API documentation context.
- If executable code, HTTP method, headers, or endpoint are requested,
  respond with structured and precise information.
- If the answer is not found in the context, say "I don't know".
- Do NOT hallucinate endpoints or parameters.
"""


def build_messages(query, retrieved_docs, chat_history):
    """
    query: str
    retrieved_docs: List[Document]
    chat_history: List[BaseMessage]
    """

    context = "\n\n".join(
        [doc.page_content for doc in retrieved_docs]
    )

    messages = []

    # System message
    messages.append(SystemMessage(content=SYSTEM_PROMPT))

    # Add previous chat history
    for msg in chat_history:
        messages.append(msg)

    # Current user query
    messages.append(
        HumanMessage(
            content=f"""
Context:
{context}

User Question:
{query}
"""
        )
    )

    return messages
