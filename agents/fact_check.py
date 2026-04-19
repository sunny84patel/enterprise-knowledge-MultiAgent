"""
agents/fact_check.py — Fact Check Agent  (from Repo 2)
Verifies whether retrieved documents actually support answering the query.
Returns True if docs are relevant and sufficient, False otherwise.
"""

from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from core.llm_factory import get_llm


FACT_CHECK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a document relevance evaluator.
Given a user query and a set of retrieved documents, determine if the documents
contain sufficient information to accurately answer the query.

Respond with ONLY: yes or no

- yes → documents contain relevant, sufficient information
- no  → documents are off-topic, empty, or insufficient"""),
    ("human", """Query: {query}

Retrieved documents:
{context}

Are these documents sufficient to answer the query? (yes/no):"""),
])


class FactCheckAgent:
    def __init__(self):
        self.llm = get_llm()
        self.chain = FACT_CHECK_PROMPT | self.llm

    async def run(self, query: str, docs: List[Document]) -> bool:
        if not docs:
            return False

        context = "\n---\n".join(
            [f"[Doc {i+1}]: {doc.page_content[:300]}" for i, doc in enumerate(docs[:4])]
        )

        response = await self.chain.ainvoke({"query": query, "context": context})
        verdict = response.content.strip().lower()
        return verdict.startswith("yes")
