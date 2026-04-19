"""
agents/web_search.py — Web Search Fallback Agent  (from Repo 2)
Uses Tavily Search API when the internal knowledge base can't answer.
Falls back to a simple DuckDuckGo search if Tavily key is not set.
"""

from typing import List
from langchain_core.documents import Document
from config import settings


class WebSearchAgent:
    def __init__(self):
        self.use_tavily = bool(settings.TAVILY_API_KEY)

    async def run(self, query: str) -> List[Document]:
        if self.use_tavily:
            return await self._tavily_search(query)
        return await self._duckduckgo_search(query)

    async def _tavily_search(self, query: str) -> List[Document]:
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
        results = await client.search(query, max_results=4)
        return [
            Document(
                page_content=r["content"],
                metadata={"source": r["url"], "title": r.get("title", ""), "type": "web"}
            )
            for r in results.get("results", [])
        ]

    async def _duckduckgo_search(self, query: str) -> List[Document]:
        """Free fallback — no API key needed."""
        try:
            from duckduckgo_search import AsyncDDGS
            async with AsyncDDGS() as ddgs:
                results = [r async for r in ddgs.text(query, max_results=4)]
            return [
                Document(
                    page_content=r["body"],
                    metadata={"source": r["href"], "title": r.get("title", ""), "type": "web"}
                )
                for r in results
            ]
        except Exception:
            return []
