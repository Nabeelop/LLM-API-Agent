from langchain.retrievers import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from langchain.schema import Document


API_QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""
You are an expert API documentation assistant.

Given a user question, generate multiple focused search queries
that would help retrieve the most relevant API documentation.

Focus on:
- API endpoints
- HTTP methods (GET, POST, PUT, DELETE)
- Authentication
- Request/Response format
- Executable code or curl examples

User question:
{question}

Generate 3–5 search queries:
"""
)


def build_api_retriever(llm, vectorstore):
    """
    Returns an advanced retriever optimized for API documentation.
    """

    base_retriever = vectorstore.as_retriever(
        search_type="mmr",        # better diversity than similarity
        search_kwargs={
            "k": 8,
            "fetch_k": 20
        }
    )

    api_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=API_QUERY_PROMPT
    )

    return api_retriever
