"""
agents/router.py — Query Router Agent  (from Repo 2)
Decides whether a query should go to:
  - "retrieval"  → use internal Qdrant knowledge base
  - "web_search" → use Tavily for current / external info
  - "direct"     → LLM can answer without retrieval (greetings, math, etc.)
"""

from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_llm


ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a query routing expert. Classify the user query into exactly one of:
- retrieval   → query needs internal knowledge base (company docs, legal, HR, technical docs)
- web_search  → query needs current/real-time information from the web
- direct      → query can be answered directly without any retrieval (greetings, simple math, general knowledge)

Respond with ONLY the single word: retrieval, web_search, or direct."""),
    ("human", "{query}"),
])


class RouterAgent:
    def __init__(self):
        self.llm = get_llm()
        self.chain = ROUTER_PROMPT | self.llm

    async def run(self, query: str) -> str:
        response = await self.chain.ainvoke({"query": query})
        route = response.content.strip().lower()
        if route not in ("retrieval", "web_search", "direct"):
            return "retrieval"   # safe default
        return route
