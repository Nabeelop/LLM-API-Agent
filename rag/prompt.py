def build_messages(query, retrieved_docs, chat_history):
    context = "\n\n".join(
        f"### DOCUMENT {i+1}\n{doc.page_content}"
        for i, doc in enumerate(retrieved_docs)
    ) if retrieved_docs else "EMPTY"

    history = "\n".join(
        f"User: {q}\nAssistant: {a}"
        for q, a in chat_history[-6:]
    ) if chat_history else "None"

    prompt = f"""
You are a helpful and intelligent AI assistant equipped with an execution environment and knowledge retrieval.

Guidelines:
- If the user asks a question that can be answered by the API Documentation below, use the documentation to answer it accurately.
- If the API Documentation is empty or irrelevant, simply answer the user's question directly or engage in normal conversation.
- Do not reveal internal reasoning or thoughts, just provide the final answer.
- If the user asks you to write Python code, output ONLY Python code wrapped strictly inside the following tags so it can be executed:
  <EXECUTE_PYTHON>
  ...
  </EXECUTE_PYTHON>
- Do NOT use standard markdown code blocks for executable code if you can use the EXECUTE_PYTHON tags.
- Do NOT use markdown code blocks.

Chat History:
{history}

API Documentation:
{context}

User Question:
{query}

Answer clearly and concisely.
"""
    return prompt.strip()
