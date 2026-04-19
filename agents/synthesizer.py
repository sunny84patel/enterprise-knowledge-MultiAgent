"""
agents/synthesizer.py — Answer Synthesis Agent  (from Repo 1 + Repo 2)
Generates the final answer using retrieved context and conversation memory.
"""

from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from core.llm_factory import get_llm
from core.memory import ConversationMemory


SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful, accurate enterprise knowledge assistant.
Use ONLY the provided context to answer the question.
If the context doesn't contain the answer, say "I don't have enough information in my knowledge base."

Rules:
- Cite sources using [Doc N] notation when referencing specific facts
- Be concise but complete
- Do not hallucinate or add information not in the context
- If the question is a follow-up, use the conversation history

Context:
{context}

Conversation history:
{history}"""),
    ("human", "{query}"),
])

DIRECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer concisely and accurately.\n\nConversation history:\n{history}"),
    ("human", "{query}"),
])


class SynthesizerAgent:
    def __init__(self):
        self.llm = get_llm()
        self.synthesis_chain = SYNTHESIS_PROMPT | self.llm
        self.direct_chain = DIRECT_PROMPT | self.llm
        self.memory = ConversationMemory()

    async def run(self, query: str, docs: List[Document], messages: list) -> str:
        context = "\n---\n".join(
            [f"[Doc {i+1}] (source: {doc.metadata.get('source', 'unknown')}):\n{doc.page_content}"
             for i, doc in enumerate(docs)]
        )
        history = self.memory.format(messages)
        response = await self.synthesis_chain.ainvoke({
            "query": query,
            "context": context,
            "history": history,
        })
        return response.content.strip()

    async def run_direct(self, query: str, messages: list) -> str:
        history = self.memory.format(messages)
        response = await self.direct_chain.ainvoke({"query": query, "history": history})
        return response.content.strip()
