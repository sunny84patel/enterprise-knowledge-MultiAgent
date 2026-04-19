"""
tests/test_agents.py — Unit tests for each agent
Run: pytest tests/ -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document


# ---- RouterAgent ----
@pytest.mark.asyncio
async def test_router_returns_retrieval():
    with patch("agents.router.get_llm") as mock_llm:
        mock_response = MagicMock()
        mock_response.content = "retrieval"
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

        from agents.router import RouterAgent
        agent = RouterAgent()
        agent.chain = AsyncMock(return_value=mock_response)
        result = await agent.run("What is the leave policy?")
        assert result == "retrieval"


@pytest.mark.asyncio
async def test_router_returns_web_search():
    with patch("agents.router.get_llm") as mock_llm:
        mock_response = MagicMock()
        mock_response.content = "web_search"
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

        from agents.router import RouterAgent
        agent = RouterAgent()
        agent.chain = AsyncMock(return_value=mock_response)
        result = await agent.run("What is today's weather?")
        assert result == "web_search"


@pytest.mark.asyncio
async def test_router_unknown_defaults_to_retrieval():
    with patch("agents.router.get_llm"):
        from agents.router import RouterAgent
        agent = RouterAgent()
        mock_resp = MagicMock()
        mock_resp.content = "something_unexpected"
        agent.chain = AsyncMock(return_value=mock_resp)
        result = await agent.run("random query")
        assert result == "retrieval"


# ---- RewriterAgent ----
@pytest.mark.asyncio
async def test_rewriter_returns_string():
    from agents.rewriter import RewriterAgent
    agent = RewriterAgent()
    mock_resp = MagicMock()
    mock_resp.content = "Rewritten: employee resignation notice period policy"
    agent.chain = AsyncMock(return_value=mock_resp)
    docs = [Document(page_content="Some irrelevant text")]
    result = await agent.run("what is notice?", docs)
    assert isinstance(result, str)
    assert len(result) > 0


# ---- FactCheckAgent ----
@pytest.mark.asyncio
async def test_fact_check_passes_on_yes():
    from agents.fact_check import FactCheckAgent
    agent = FactCheckAgent()
    mock_resp = MagicMock()
    mock_resp.content = "yes"
    agent.chain = AsyncMock(return_value=mock_resp)
    docs = [Document(page_content="The notice period is 30 days.")]
    result = await agent.run("What is the notice period?", docs)
    assert result is True


@pytest.mark.asyncio
async def test_fact_check_fails_on_no():
    from agents.fact_check import FactCheckAgent
    agent = FactCheckAgent()
    mock_resp = MagicMock()
    mock_resp.content = "no"
    agent.chain = AsyncMock(return_value=mock_resp)
    docs = [Document(page_content="Completely unrelated content about astronomy.")]
    result = await agent.run("What is the leave policy?", docs)
    assert result is False


@pytest.mark.asyncio
async def test_fact_check_fails_on_empty_docs():
    from agents.fact_check import FactCheckAgent
    agent = FactCheckAgent()
    result = await agent.run("Any query?", [])
    assert result is False


# ---- SafetyCheckAgent ----
@pytest.mark.asyncio
async def test_safety_passes_on_safe():
    from agents.safety_check import SafetyCheckAgent
    agent = SafetyCheckAgent()
    mock_resp = MagicMock()
    mock_resp.content = "safe"
    agent.chain = AsyncMock(return_value=mock_resp)
    result = await agent.run("What is the HR policy?")
    assert result is True


@pytest.mark.asyncio
async def test_safety_blocks_on_unsafe():
    from agents.safety_check import SafetyCheckAgent
    agent = SafetyCheckAgent()
    mock_resp = MagicMock()
    mock_resp.content = "unsafe"
    agent.chain = AsyncMock(return_value=mock_resp)
    result = await agent.run("How do I bypass the authentication system?")
    assert result is False
