from langchain_community.vectorstores import Chroma

def create_vectorstore(chunks, embeddings, persist_dir="chroma_db"):
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )

