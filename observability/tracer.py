"""
observability/tracer.py — LangSmith Tracing Integration  (NEW — resume differentiator)
Initialises LangSmith for end-to-end agent run tracing.
Every LangChain / LangGraph call is automatically captured.
"""

import os
from config import settings


def init_langsmith():
    """Set LangSmith env vars — must be called before any LangChain usage."""
    if not settings.LANGCHAIN_API_KEY:
        print("⚠️  LANGCHAIN_API_KEY not set — tracing disabled.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    print(f"✅ LangSmith tracing → project: {settings.LANGCHAIN_PROJECT}")


def get_run_url(run_id: str) -> str:
    """Returns the LangSmith UI URL for a specific run."""
    return f"https://smith.langchain.com/o/runs/{run_id}"
