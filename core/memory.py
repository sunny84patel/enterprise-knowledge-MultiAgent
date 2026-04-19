"""
core/memory.py — Conversation Memory  (from Repo 1)
Summarises long conversation history to stay within context window.
"""

from typing import List
from langchain_core.messages import HumanMessage, AIMessage


class ConversationMemory:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns

    def format(self, messages: List[dict]) -> str:
        """Format last N turns of conversation as a readable string."""
        if not messages:
            return "No previous conversation."

        recent = messages[-self.max_turns * 2:]
        lines = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(lines)

    def to_langchain(self, messages: List[dict]):
        """Convert to LangChain message objects."""
        result = []
        for msg in messages:
            if msg.get("role") == "user":
                result.append(HumanMessage(content=msg["content"]))
            else:
                result.append(AIMessage(content=msg["content"]))
        return result
