"""
eval/benchmark_report.py — Before/After Benchmark Report  (NEW)
Compares baseline RAG (no rewriting, no fact check) vs full multi-agent pipeline.
This is how you generate the "improved accuracy by X%" number for your resume.

Run:  python eval/benchmark_report.py
"""

import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from ragas import evaluate
from ragas.metrics import context_precision, faithfulness, answer_relevancy
from ragas.run_config import RunConfig
from datasets import Dataset

from agents.graph import build_graph
from core.retriever import HybridRetriever
from core.llm_factory import get_embeddings, get_llm
from core.ragas_utils import mean_metric_scores
from langchain_core.prompts import ChatPromptTemplate

EVAL_QUESTIONS = [
    "What is the employee leave policy?",
    "What are the data retention requirements?",
    "Explain the legal complaint filing process.",
    "What is the probation period for new hires?",
    "How are performance reviews conducted?",
]

SIMPLE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Answer using only the context.\n\nContext: {context}"),
    ("human", "{query}"),
])


async def run_baseline(questions):
    """Simple retrieval → LLM, no agents."""
    retriever = HybridRetriever()
    llm = get_llm()
    chain = SIMPLE_PROMPT | llm
    answers, contexts = [], []

    for q in questions:
        docs = await retriever.retrieve(q, top_k=3)
        context = "\n".join([d.page_content for d in docs])
        resp = await chain.ainvoke({"query": q, "context": context})
        answers.append(resp.content)
        contexts.append([d.page_content for d in docs])

    return answers, contexts


async def run_full_pipeline(questions):
    """Full multi-agent pipeline with rewriting + fact check."""
    graph = build_graph()
    answers, contexts = [], []

    for q in questions:
        result = await graph.ainvoke({
            "query": q, "session_id": "bench",
            "messages": [], "retrieved_docs": [],
            "rewritten_query": None, "rewrite_attempts": 0,
            "route": None, "fact_check_passed": None,
            "safety_passed": None, "final_answer": None,
            "agent_trace": [],
        })
        answers.append(result.get("final_answer", ""))
        contexts.append([d.page_content for d in result.get("retrieved_docs", [])])

    return answers, contexts


async def main():
    ground_truths = ["N/A"] * len(EVAL_QUESTIONS)   # replace with real GT for best results

    print("Running baseline (simple RAG)...")
    base_answers, base_contexts = await run_baseline(EVAL_QUESTIONS)

    print("Running full multi-agent pipeline...")
    full_answers, full_contexts = await run_full_pipeline(EVAL_QUESTIONS)

    def score(answers, contexts):
        ds = Dataset.from_dict({
            "question": EVAL_QUESTIONS,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })
        raw = evaluate(
            ds,
            metrics=[context_precision, faithfulness, answer_relevancy],
            llm=get_llm(),
            embeddings=get_embeddings(),
            run_config=RunConfig(timeout=300),
        )
        return mean_metric_scores(raw)

    print("\nScoring baseline...")
    base_scores = score(base_answers, base_contexts)

    print("Scoring full pipeline...")
    full_scores = score(full_answers, full_contexts)

    report = {
        "baseline": base_scores,
        "full_pipeline": full_scores,
        "improvement": {
            k: round((full_scores[k] - base_scores[k]) / max(base_scores[k], 0.001) * 100, 1)
            for k in base_scores
        },
    }

    print("\n======= BENCHMARK REPORT =======")
    for metric in base_scores:
        imp = report["improvement"][metric]
        print(f"  {metric}: {base_scores[metric]:.3f} → {full_scores[metric]:.3f}  ({'+' if imp>0 else ''}{imp}%)")

    with open("data/benchmark_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\n✅ Report saved to data/benchmark_report.json")


if __name__ == "__main__":
    asyncio.run(main())
