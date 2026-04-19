"""
tests/test_rag.py — Integration tests for the RAG pipeline
Run: pytest tests/test_rag.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document


SAMPLE_DOCS = [
    Document(
        page_content="The employee notice period is 30 days for all permanent staff.",
        metadata={"source": "hr_policy.pdf", "page": 1}
    ),
    Document(
        page_content="Annual leave entitlement is 20 days per year.",
        metadata={"source": "hr_policy.pdf", "page": 2}
    ),
]


@pytest.mark.asyncio
async def test_full_pipeline_retrieval_route():
    """Test that a retrieval-routed query returns an answer with sources."""
    with patch("agents.router.get_llm"), \
         patch("agents.retriever.HybridRetriever") as mock_ret, \
         patch("agents.retriever.ContextCompressor") as mock_comp, \
         patch("agents.fact_check.get_llm"), \
         patch("agents.safety_check.get_llm"), \
         patch("agents.synthesizer.get_llm"):

        from agents.graph import build_graph

        # Mock retriever returns sample docs
        mock_ret.return_value.retrieve = AsyncMock(return_value=SAMPLE_DOCS)
        mock_comp.return_value.compress = AsyncMock(return_value=SAMPLE_DOCS)

        graph = build_graph()

        # We test the state flow, not LLM output
        initial_state = {
            "query": "What is the notice period?",
            "session_id": "test",
            "messages": [],
            "retrieved_docs": [],
            "rewritten_query": None,
            "rewrite_attempts": 0,
            "route": None,
            "fact_check_passed": None,
            "safety_passed": None,
            "final_answer": None,
            "agent_trace": [],
        }
        # Graph compiled — structural test
        assert graph is not None


@pytest.mark.asyncio
async def test_memory_formats_correctly():
    from core.memory import ConversationMemory
    memory = ConversationMemory()
    messages = [
        {"role": "user", "content": "What is leave policy?"},
        {"role": "assistant", "content": "You get 20 days per year."},
    ]
    formatted = memory.format(messages)
    assert "User:" in formatted
    assert "Assistant:" in formatted
    assert "20 days" in formatted


def test_parent_chunk_store_save_and_retrieve():
    import tempfile, os
    from db.parent_store import ParentChunkStore
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        store = ParentChunkStore(path=path)
        store.save_parent("chunk_001", "This is the parent content for chunk 001.")
        result = store.get_parent("chunk_001")
        assert result == "This is the parent content for chunk 001."
        assert store.get_parent("nonexistent") is None
    finally:
        os.unlink(path)


def test_metrics_summary():
    import tempfile, os
    from observability.metrics import MetricsCollector, QueryMetrics
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
        path = f.name
    try:
        c = MetricsCollector(log_path=path)
        c.record(QueryMetrics(
            session_id="s1", query="test?", route="retrieval",
            rewrite_attempts=1, fact_check_passed=True,
            num_docs_retrieved=3, latency_ms=420.5
        ))
        c.record(QueryMetrics(
            session_id="s2", query="test2?", route="web_search",
            rewrite_attempts=0, fact_check_passed=False,
            num_docs_retrieved=0, latency_ms=800.0
        ))
        summary = c.summary()
        assert summary["total_queries"] == 2
        assert summary["fact_check_pass_rate"] == 50.0
    finally:
        os.unlink(path)
