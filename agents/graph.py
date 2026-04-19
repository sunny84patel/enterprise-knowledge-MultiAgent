"""
agents/graph.py — LangGraph State Machine
Wires all agents into a directed graph with conditional routing.

Flow:
  router → retriever → rewriter (if needed) → fact_check → safety_check → synthesizer

From Repo 1: query rewriting loop, memory, modular LLM swapping
From Repo 2: router, fact_check, safety_check, web_search fallback
"""

from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
import operator

from agents.router import RouterAgent
from agents.retriever import RetrieverAgent
from agents.rewriter import RewriterAgent
from agents.fact_check import FactCheckAgent
from agents.safety_check import SafetyCheckAgent
from agents.synthesizer import SynthesizerAgent
from agents.web_search import WebSearchAgent


# ---------- Shared State ----------
class AgentState(TypedDict):
    query: str
    session_id: str
    messages: List[dict]
    retrieved_docs: List[Document]
    rewritten_query: Optional[str]
    rewrite_attempts: int
    route: Optional[str]           # "retrieval" | "web_search" | "direct"
    fact_check_passed: Optional[bool]
    safety_passed: Optional[bool]
    final_answer: Optional[str]
    agent_trace: Annotated[List[str], operator.add]


# ---------- Node Functions ----------
router_agent = RouterAgent()
retriever_agent = RetrieverAgent()
rewriter_agent = RewriterAgent()
fact_check_agent = FactCheckAgent()
safety_check_agent = SafetyCheckAgent()
synthesizer_agent = SynthesizerAgent()
web_search_agent = WebSearchAgent()


async def run_router(state: AgentState) -> AgentState:
    route = await router_agent.run(state["query"])
    return {**state, "route": route, "agent_trace": [f"[Router] → {route}"]}


async def run_retriever(state: AgentState) -> AgentState:
    query = state.get("rewritten_query") or state["query"]
    docs = await retriever_agent.run(query)
    return {**state, "retrieved_docs": docs, "agent_trace": [f"[Retriever] → {len(docs)} docs"]}


async def run_web_search(state: AgentState) -> AgentState:
    docs = await web_search_agent.run(state["query"])
    return {**state, "retrieved_docs": docs, "agent_trace": ["[WebSearch] → fallback results"]}


async def run_rewriter(state: AgentState) -> AgentState:
    attempts = state.get("rewrite_attempts", 0) + 1
    rewritten = await rewriter_agent.run(state["query"], state["retrieved_docs"])
    return {
        **state,
        "rewritten_query": rewritten,
        "rewrite_attempts": attempts,
        "agent_trace": [f"[Rewriter] → attempt {attempts}: '{rewritten}'"],
    }


async def run_fact_check(state: AgentState) -> AgentState:
    passed = await fact_check_agent.run(
        state.get("rewritten_query") or state["query"],
        state["retrieved_docs"]
    )
    return {**state, "fact_check_passed": passed, "agent_trace": [f"[FactCheck] → {'passed' if passed else 'failed'}"]}


async def run_safety_check(state: AgentState) -> AgentState:
    passed = await safety_check_agent.run(state["query"])
    return {**state, "safety_passed": passed, "agent_trace": [f"[Safety] → {'ok' if passed else 'blocked'}"]}


async def run_synthesizer(state: AgentState) -> AgentState:
    answer = await synthesizer_agent.run(
        state.get("rewritten_query") or state["query"],
        state["retrieved_docs"],
        state["messages"]
    )
    return {**state, "final_answer": answer, "agent_trace": ["[Synthesizer] → answer generated"]}


async def run_direct_answer(state: AgentState) -> AgentState:
    answer = await synthesizer_agent.run_direct(state["query"], state["messages"])
    return {**state, "final_answer": answer, "agent_trace": ["[Synthesizer] → direct answer"]}


async def run_blocked(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer": "I'm sorry, I can't help with that request.",
        "agent_trace": ["[Safety] → request blocked"],
    }


# ---------- Conditional Edges ----------
def route_after_router(state: AgentState) -> str:
    return state.get("route", "retrieval")


def route_after_retriever(state: AgentState) -> str:
    """If docs are poor quality, rewrite. Otherwise fact_check."""
    docs = state.get("retrieved_docs", [])
    attempts = state.get("rewrite_attempts", 0)
    if len(docs) == 0 and attempts < 2:
        return "rewrite"
    return "fact_check"


def route_after_rewriter(state: AgentState) -> str:
    return "retriever"


def route_after_fact_check(state: AgentState) -> str:
    if state.get("fact_check_passed"):
        return "synthesizer"
    attempts = state.get("rewrite_attempts", 0)
    if attempts < 2:
        return "rewrite"
    return "synthesizer"   # best-effort after max attempts


def route_after_safety(state: AgentState) -> str:
    return "retriever" if state.get("safety_passed") else "blocked"


# ---------- Build Graph ----------
def build_graph():
    g = StateGraph(AgentState)

    g.add_node("router", run_router)
    g.add_node("retriever", run_retriever)
    g.add_node("web_search", run_web_search)
    g.add_node("rewriter", run_rewriter)
    g.add_node("fact_check", run_fact_check)
    g.add_node("safety_check", run_safety_check)
    g.add_node("synthesizer", run_synthesizer)
    g.add_node("direct_answer", run_direct_answer)
    g.add_node("blocked", run_blocked)

    g.set_entry_point("safety_check")

    g.add_conditional_edges("safety_check", route_after_safety, {
        "retriever": "router",
        "blocked": "blocked",
    })
    g.add_conditional_edges("router", route_after_router, {
        "retrieval": "retriever",
        "web_search": "web_search",
        "direct": "direct_answer",
    })
    g.add_conditional_edges("retriever", route_after_retriever, {
        "rewrite": "rewriter",
        "fact_check": "fact_check",
    })
    g.add_edge("rewriter", "retriever")
    g.add_edge("web_search", "fact_check")
    g.add_conditional_edges("fact_check", route_after_fact_check, {
        "synthesizer": "synthesizer",
        "rewrite": "rewriter",
    })
    g.add_edge("synthesizer", END)
    g.add_edge("direct_answer", END)
    g.add_edge("blocked", END)

    return g.compile()
