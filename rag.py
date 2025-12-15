from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


def main():

    loader = PyPDFLoader("sample.pdf")
    documents = loader.load()
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
        task="text-generation"
    )
    llm = ChatHuggingFace(llm=hf_endpoint)

    print("PDF loaded. Ask questions (type 'exit' to quit)\n")

   
    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break

        docs = retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)

        prompt = f"""
Use ONLY the context below.
Do NOT invent information.

Context:
{context}

Question:
{query}
"""

        response = llm.invoke(prompt)
        print("\nAssistant:", response.content, "\n")


if __name__ == "__main__":
    main()

