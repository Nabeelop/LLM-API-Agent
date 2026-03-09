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
            "k": 4,           # Get the top 4 distinct chunks
            "fetch_k": 10,    # Search through 10 candidates first
            "lambda_mult": 0.7 # 0.5 is very diverse, 1.0 is pure similarity. 0.7 is the sweet spot.
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
