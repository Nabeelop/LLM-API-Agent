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
You are an expert API documentation assistant.

Rules:
- Do not reveal internal reasoning or thoughts.
- Answer strictly using the provided API documentation.
- If the API Documentation section is EMPTY or the answer cannot be derived, reply exactly:
  "Not found in documentation"
- Do not assume, guess, or invent information.
- Prefer executable examples (curl, Python, JavaScript).
- If Python execution is required, output ONLY Python code wrapped strictly inside:
  <EXECUTE_PYTHON>
  ...
  </EXECUTE_PYTHON>
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
