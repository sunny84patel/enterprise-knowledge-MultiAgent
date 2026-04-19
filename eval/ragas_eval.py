"""
eval/ragas_eval.py — RAGAS Retrieval Evaluation  (NEW — resume differentiator)
Measures:
  - Context Precision    → how relevant are retrieved chunks?
  - Context Recall       → are all needed facts retrieved?
  - Answer Faithfulness  → does the answer stay within retrieved context?
  - Answer Relevancy     → does the answer actually address the question?

Run: python eval/ragas_eval.py
Reports before/after accuracy scores you can put on your resume.
"""

import asyncio
import json
import sys
from pathlib import Path

# Project root must be on path when running as `python eval/ragas_eval.py`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

from agents.graph import build_graph
from core.llm_factory import get_embeddings, get_llm
from core.ragas_utils import mean_metric_scores


# --- Sample evaluation questions (replace with domain-specific ones) ---
EVAL_QUESTIONS = [
    {
        "question": "What is the notice period for employee resignation?",
        "ground_truth": "The standard notice period is 30 days for most roles.",
    },
    {
        "question": "What are the data retention policies for customer records?",
        "ground_truth": "Customer records must be retained for a minimum of 7 years.",
    },
    {
        "question": "What is the process for filing a legal complaint?",
        "ground_truth": "Complaints must be filed within 60 days using Form L-101.",
    },
]


async def run_eval():
    graph = build_graph()
    questions, answers, contexts, ground_truths = [], [], [], []

    for item in EVAL_QUESTIONS:
        result = await graph.ainvoke({
            "query": item["question"],
            "session_id": "eval",
            "messages": [],
            "retrieved_docs": [],
            "rewritten_query": None,
            "rewrite_attempts": 0,
            "route": None,
            "fact_check_passed": None,
            "safety_passed": None,
            "final_answer": None,
            "agent_trace": [],
        })
        questions.append(item["question"])
        answers.append(result.get("final_answer", ""))
        contexts.append([doc.page_content for doc in result.get("retrieved_docs", [])])
        ground_truths.append(item["ground_truth"])
        print(f"✅ Evaluated: {item['question'][:60]}...")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    print("\n📊 Running RAGAS evaluation...\n")
    result = evaluate(
        dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
        llm=get_llm(),
        embeddings=get_embeddings(),
        run_config=RunConfig(timeout=300),
    )
    scores = mean_metric_scores(result)

    print("\n=== RAGAS Scores ===")
    for metric, value in scores.items():
        print(f"  {metric}: {value:.3f}")

    with open("data/ragas_results.json", "w") as f:
        json.dump(scores, f, indent=2)
    print("\n✅ Results saved to data/ragas_results.json")
    return scores


if __name__ == "__main__":
    asyncio.run(run_eval())
