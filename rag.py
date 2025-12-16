import os
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


def main():

    documents = []
    pdf_folder = "pdfs"

    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_folder, file))
            documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    hf_endpoint = HuggingFaceEndpoint(
        repo_id="deepseek-ai/DeepSeek-V3.2",
        task="text-generation",
        max_new_tokens=300,
        temperature=0.2
    )
    llm = ChatHuggingFace(llm=hf_endpoint)

    print("PDFs loaded. Ask questions (type 'exit' to quit)\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break

        docs = retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)

        prompt = f"""
You are a smart LLLM API Agent
Use ONLY the context below.


Context:
{context}

Question:
{query}
Based on the context,fulfill the user's query if user requests code from API documentation,generate based on the context
"""

        response = llm.invoke(prompt)
        print("\nAssistant:", response.content, "\n")


if __name__ == "__main__":
    main()
