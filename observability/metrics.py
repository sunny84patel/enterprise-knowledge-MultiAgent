"""
observability/metrics.py — Accuracy & Latency Metrics  (NEW — resume differentiator)
Tracks per-query metrics so you can report "improved accuracy by X%"
with real numbers backed by this module.
"""

import time
import json
import os
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

METRICS_LOG = "data/metrics_log.jsonl"


@dataclass
class QueryMetrics:
    session_id: str
    query: str
    route: str
    rewrite_attempts: int
    fact_check_passed: bool
    num_docs_retrieved: int
    latency_ms: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_rating: Optional[int] = None   # 1-5 thumbs from UI


class MetricsCollector:
    def __init__(self, log_path: str = METRICS_LOG):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._start_time: Optional[float] = None

    def start_timer(self):
        self._start_time = time.perf_counter()

    def elapsed_ms(self) -> float:
        if self._start_time is None:
            return 0.0
        return (time.perf_counter() - self._start_time) * 1000

    def record(self, metrics: QueryMetrics):
        with open(self.log_path, "a") as f:
            f.write(json.dumps(asdict(metrics)) + "\n")

    def load_all(self):
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    def summary(self) -> dict:
        records = self.load_all()
        if not records:
            return {}
        total = len(records)
        fact_pass = sum(1 for r in records if r.get("fact_check_passed"))
        avg_latency = sum(r["latency_ms"] for r in records) / total
        avg_rewrites = sum(r["rewrite_attempts"] for r in records) / total
        routes = {}
        for r in records:
            routes[r["route"]] = routes.get(r["route"], 0) + 1
        return {
            "total_queries": total,
            "fact_check_pass_rate": round(fact_pass / total * 100, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "avg_rewrite_attempts": round(avg_rewrites, 2),
            "route_distribution": routes,
        }


# Singleton
collector = MetricsCollector()
