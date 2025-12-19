from langchain_core.documents import Document
from typing import List


class APIDocumentRetriever:
    """
    Custom retriever optimized for API documentation.
    Avoids MultiQueryRetriever to stay compatible with HF providers.
    """

    def __init__(self, vectorstore):
        self.retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 6,
                "fetch_k": 20
            }
        )

    def invoke(self, query: str) -> List[Document]:
        api_boost = (
            f"{query}\n"
            "Focus on API endpoint, HTTP method, authentication, "
            "request body, response schema, curl example, executable code."
        )

        return self.retriever.invoke(api_boost)


def build_api_retriever(vectorstore):
    return APIDocumentRetriever(vectorstore)
