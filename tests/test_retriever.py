"""Unit tests for rag/retriever.py.

Tests Jaccard similarity, deduplication logic, and the APIDocumentRetriever
class without requiring a live vector store.
"""

import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

from rag.retriever import _jaccard_similarity, _deduplicate_chunks, APIDocumentRetriever


# ─── Jaccard Similarity ───────────────────────────────────────────────────────

class TestJaccardSimilarity:
    def test_identical_strings(self):
        assert _jaccard_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert _jaccard_similarity("apple banana", "cat dog") == 0.0

    def test_partial_overlap(self):
        score = _jaccard_similarity("a b c", "b c d")
        # intersection={b,c}, union={a,b,c,d} → 2/4 = 0.5
        assert abs(score - 0.5) < 1e-9

    def test_empty_string_a(self):
        assert _jaccard_similarity("", "hello") == 0.0

    def test_empty_string_b(self):
        assert _jaccard_similarity("hello", "") == 0.0

    def test_case_insensitive(self):
        # "Hello" and "hello" should be treated as the same word
        assert _jaccard_similarity("Hello World", "hello world") == 1.0


# ─── Deduplicate Chunks ───────────────────────────────────────────────────────

class TestDeduplicateChunks:
    def _doc(self, text: str) -> Document:
        return Document(page_content=text)

    def test_empty_list(self):
        assert _deduplicate_chunks([]) == []

    def test_single_doc(self):
        docs = [self._doc("unique content here")]
        result = _deduplicate_chunks(docs)
        assert len(result) == 1

    def test_identical_docs_removed(self):
        text = "GET /api/v1/users returns list of users with pagination"
        docs = [self._doc(text), self._doc(text)]
        result = _deduplicate_chunks(docs, threshold=0.70)
        assert len(result) == 1

    def test_distinct_docs_kept(self):
        docs = [
            self._doc("GET /users returns list of users"),
            self._doc("POST /auth/token authenticates with username and password"),
        ]
        result = _deduplicate_chunks(docs, threshold=0.70)
        assert len(result) == 2

    def test_high_threshold_keeps_near_duplicates(self):
        """With threshold=1.0 (only exact duplicates removed), near-dupes are kept."""
        docs = [
            self._doc("hello world foo bar"),
            self._doc("hello world foo baz"),
        ]
        result = _deduplicate_chunks(docs, threshold=1.0)
        assert len(result) == 2

    def test_low_threshold_removes_near_duplicates(self):
        """With threshold=0.5 loose threshold removes near-identical docs."""
        docs = [
            self._doc("hello world foo bar"),
            self._doc("hello world foo baz"),
        ]
        result = _deduplicate_chunks(docs, threshold=0.5)
        assert len(result) == 1


# ─── APIDocumentRetriever ─────────────────────────────────────────────────────

class TestAPIDocumentRetriever:
    def _make_retriever(self, docs):
        """Build an APIDocumentRetriever backed by a mock vectorstore."""
        mock_base = MagicMock()
        mock_base.invoke.return_value = docs

        mock_vs = MagicMock()
        mock_vs.as_retriever.return_value = mock_base

        return APIDocumentRetriever(mock_vs)

    def test_invoke_returns_deduped_docs(self):
        text = "endpoint GET /items returns paginated items list"
        docs = [Document(page_content=text), Document(page_content=text)]
        retriever = self._make_retriever(docs)
        result = retriever.invoke("list items")
        assert len(result) == 1

    def test_invoke_with_distinct_docs(self):
        docs = [
            Document(page_content="POST /auth/login authenticates user credentials"),
            Document(page_content="GET /products returns all available products list"),
        ]
        retriever = self._make_retriever(docs)
        result = retriever.invoke("login")
        assert len(result) == 2

    def test_mmr_kwargs_configured(self):
        """Retriever must configure MMR search with λ=0.7 and k=4."""
        mock_vs = MagicMock()
        APIDocumentRetriever(mock_vs)
        call_kwargs = mock_vs.as_retriever.call_args[1]
        assert call_kwargs["search_type"] == "mmr"
        assert call_kwargs["search_kwargs"]["lambda_mult"] == 0.7
        assert call_kwargs["search_kwargs"]["k"] == 4
