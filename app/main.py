from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

from rag.loader import load_pdf
from rag.splitter import split_documents
from rag.embeddings import get_embeddings
from rag.vector_store import create_vectorstore
from rag.retriever import build_api_retriever
from rag.prompt import build_messages


def main():
    # -------- Load & Process Docs --------
    docs = load_pdf("data/pdfs")
    chunks = split_documents(docs)

    embeddings = get_embeddings()
    vectorstore = create_vectorstore(chunks, embeddings)

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
    chat_history = []

    print("\n🚀 Smart API Agent Ready (type 'exit')\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break

        retrieved_docs = retriever.invoke(query)

        prompt = build_messages(
            query=query,
            retrieved_docs=retrieved_docs,
            chat_history=chat_history
        )

        response = chat_model.invoke(prompt)

        print("\nAgent:\n", response.content, "\n")

        # save history as plain text
        chat_history.append(f"User: {query}")
        chat_history.append(f"Agent: {response.content}")


if __name__ == "__main__":
    main()
