"""Helpers for RAGAS EvaluationResult (aggregate scores are not a dict)."""

from ragas.dataset_schema import EvaluationResult
from ragas.utils import safe_nanmean


def mean_metric_scores(result: EvaluationResult) -> dict[str, float]:
    if not result.scores:
        return {}
    keys = result.scores[0].keys()
    return {
        k: float(safe_nanmean([row[k] for row in result.scores]))
        for k in keys
    }
