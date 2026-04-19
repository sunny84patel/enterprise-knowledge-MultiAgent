"""
agents/rewriter.py — Query Rewriter Agent  (from Repo 2)
Self-corrects a bad query when retrieval returns poor results.
Analyzes the query + retrieved docs and reformulates for better retrieval.
"""

from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from core.llm_factory import get_llm


REWRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a search query optimization expert. 
The original query retrieved low-quality or irrelevant documents.
Your job is to rewrite the query to improve retrieval quality.

Guidelines:
- Make the query more specific and use domain-specific terminology
- Decompose complex questions into focused sub-queries
- Remove ambiguous pronouns
- Add relevant context keywords
- Output ONLY the rewritten query, no explanation"""),
    ("human", """Original query: {query}

Retrieved document snippets (low quality):
{doc_snippets}

Rewritten query:"""),
])


class RewriterAgent:
    def __init__(self):
        self.llm = get_llm()
        self.chain = REWRITER_PROMPT | self.llm

    async def run(self, query: str, docs: List[Document]) -> str:
        doc_snippets = "\n---\n".join(
            [doc.page_content[:200] for doc in docs[:3]]
        ) if docs else "No documents retrieved."

        response = await self.chain.ainvoke({
            "query": query,
            "doc_snippets": doc_snippets,
        })
        return response.content.strip()
